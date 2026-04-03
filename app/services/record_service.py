from collections.abc import Sequence
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.models.financial_record import EntryType, FinancialRecord
from app.models.user import User, UserRole
from app.schemas.analytics import CategoryStatRow, RecordStatsSummary
from app.schemas.financial_record import FinancialRecordCreate, FinancialRecordUpdate
from app.services import dashboard_service
from app.services.query_helpers import date_filter_clause


def _active_records():
    return FinancialRecord.deleted_at.is_(None)


def _require_analyst_or_admin(user: User) -> None:
    if user.role not in (UserRole.analyst, UserRole.admin):
        raise ForbiddenError("Only analysts and admins can access this resource")


def get_by_id(db: Session, record_id: int, include_deleted: bool = False) -> FinancialRecord | None:
    q = select(FinancialRecord).where(FinancialRecord.id == record_id)
    if not include_deleted:
        q = q.where(_active_records())
    return db.scalars(q).first()


def list_records(
    db: Session,
    *,
    current_user: User,
    skip: int = 0,
    limit: int = 50,
    entry_date_from: date | None = None,
    entry_date_to: date | None = None,
    category: str | None = None,
    entry_type: EntryType | None = None,
) -> tuple[Sequence[FinancialRecord], int]:
    _require_analyst_or_admin(current_user)
    q = select(FinancialRecord).where(_active_records())

    if entry_date_from is not None:
        q = q.where(FinancialRecord.entry_date >= entry_date_from)
    if entry_date_to is not None:
        q = q.where(FinancialRecord.entry_date <= entry_date_to)
    if category:
        q = q.where(FinancialRecord.category == category)
    if entry_type is not None:
        q = q.where(FinancialRecord.entry_type == entry_type)

    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0

    q = q.order_by(FinancialRecord.entry_date.desc(), FinancialRecord.id.desc()).offset(skip).limit(limit)
    rows = db.scalars(q).all()
    return rows, total


def create_record(db: Session, data: FinancialRecordCreate, creator: User) -> FinancialRecord:
    if creator.role not in (UserRole.admin,):
        raise ForbiddenError("Only admins can create financial records")
    rec = FinancialRecord(
        amount=data.amount,
        entry_type=data.entry_type,
        category=data.category.strip(),
        entry_date=data.entry_date,
        notes=data.notes.strip() if data.notes else None,
        created_by_id=creator.id,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def update_record(db: Session, record_id: int, data: FinancialRecordUpdate, updater: User) -> FinancialRecord:
    if updater.role != UserRole.admin:
        raise ForbiddenError("Only admins can update financial records")
    rec = get_by_id(db, record_id)
    if not rec:
        raise NotFoundError("Record not found")
    if data.amount is not None:
        rec.amount = data.amount
    if data.entry_type is not None:
        rec.entry_type = data.entry_type
    if data.category is not None:
        rec.category = data.category.strip()
    if data.entry_date is not None:
        rec.entry_date = data.entry_date
    if data.notes is not None:
        rec.notes = data.notes.strip() if data.notes else None
    rec.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(rec)
    return rec


def search_records(
    db: Session,
    *,
    current_user: User,
    q: str,
    skip: int = 0,
    limit: int = 50,
) -> tuple[Sequence[FinancialRecord], int]:
    _require_analyst_or_admin(current_user)
    term = q.strip()
    if not term:
        raise AppError("Search text cannot be empty")
    pattern = f"%{term}%"
    base = select(FinancialRecord).where(
        _active_records(),
        or_(FinancialRecord.category.ilike(pattern), FinancialRecord.notes.ilike(pattern)),
    )
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    stmt = base.order_by(FinancialRecord.entry_date.desc(), FinancialRecord.id.desc()).offset(skip).limit(limit)
    rows = db.scalars(stmt).all()
    return rows, total


def record_stats_summary(
    db: Session,
    *,
    current_user: User,
    entry_date_from: date | None = None,
    entry_date_to: date | None = None,
) -> RecordStatsSummary:
    _require_analyst_or_admin(current_user)
    clause = date_filter_clause(entry_date_from, entry_date_to)
    count = db.scalar(select(func.count(FinancialRecord.id)).where(clause)) or 0
    totals = dashboard_service.get_period_totals(
        db, entry_date_from=entry_date_from, entry_date_to=entry_date_to
    )
    return RecordStatsSummary(
        count=int(count),
        total_income=totals.total_income,
        total_expense=totals.total_expense,
        net=totals.net_balance,
        date_from=entry_date_from,
        date_to=entry_date_to,
    )


def record_stats_by_category(
    db: Session,
    *,
    current_user: User,
    entry_date_from: date | None = None,
    entry_date_to: date | None = None,
) -> list[CategoryStatRow]:
    _require_analyst_or_admin(current_user)
    clause = date_filter_clause(entry_date_from, entry_date_to)
    rows = db.execute(
        select(
            FinancialRecord.category,
            FinancialRecord.entry_type,
            func.count(FinancialRecord.id),
            func.sum(FinancialRecord.amount),
        )
        .where(clause)
        .group_by(FinancialRecord.category, FinancialRecord.entry_type)
        .order_by(FinancialRecord.category, FinancialRecord.entry_type)
    ).all()
    return [
        CategoryStatRow(
            category=r[0],
            entry_type=r[1],
            entry_count=int(r[2]),
            total=Decimal(str(r[3])),
        )
        for r in rows
    ]


def soft_delete_record(db: Session, record_id: int, actor: User) -> None:
    if actor.role != UserRole.admin:
        raise ForbiddenError("Only admins can delete financial records")
    rec = get_by_id(db, record_id)
    if not rec:
        raise NotFoundError("Record not found")
    rec.deleted_at = datetime.now(timezone.utc)
    db.commit()
