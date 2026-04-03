from datetime import date

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import RequireAdmin, RequireAnalystOrAdmin
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.models.financial_record import EntryType
from app.schemas.analytics import CategoryStatRow, RecordStatsSummary
from app.schemas.financial_record import FinancialRecordCreate, FinancialRecordOut, FinancialRecordUpdate
from app.services import record_service

router = APIRouter(prefix="/records", tags=["financial-records"])


@router.get("/search", response_model=list[FinancialRecordOut])
def search_records(
    _user: RequireAnalystOrAdmin,
    response: Response,
    db: Session = Depends(get_db),
    q: str = Query(..., min_length=1, max_length=200, description="Substring match on category or notes"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[FinancialRecordOut]:
    rows, total = record_service.search_records(
        db, current_user=_user, q=q, skip=skip, limit=limit
    )
    response.headers["X-Total-Count"] = str(total)
    return [FinancialRecordOut.model_validate(r) for r in rows]


@router.get("/stats/summary", response_model=RecordStatsSummary)
def record_stats_summary(
    _user: RequireAnalystOrAdmin,
    db: Session = Depends(get_db),
    entry_date_from: date | None = None,
    entry_date_to: date | None = None,
) -> RecordStatsSummary:
    return record_service.record_stats_summary(
        db,
        current_user=_user,
        entry_date_from=entry_date_from,
        entry_date_to=entry_date_to,
    )


@router.get("/stats/by-category", response_model=list[CategoryStatRow])
def record_stats_by_category(
    _user: RequireAnalystOrAdmin,
    db: Session = Depends(get_db),
    entry_date_from: date | None = None,
    entry_date_to: date | None = None,
) -> list[CategoryStatRow]:
    return record_service.record_stats_by_category(
        db,
        current_user=_user,
        entry_date_from=entry_date_from,
        entry_date_to=entry_date_to,
    )


@router.get("", response_model=list[FinancialRecordOut])
def list_records(
    _user: RequireAnalystOrAdmin,
    response: Response,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    entry_date_from: date | None = None,
    entry_date_to: date | None = None,
    category: str | None = None,
    entry_type: EntryType | None = None,
) -> list[FinancialRecordOut]:
    rows, total = record_service.list_records(
        db,
        current_user=_user,
        skip=skip,
        limit=limit,
        entry_date_from=entry_date_from,
        entry_date_to=entry_date_to,
        category=category,
        entry_type=entry_type,
    )
    response.headers["X-Total-Count"] = str(total)
    return [FinancialRecordOut.model_validate(r) for r in rows]


@router.get("/{record_id}", response_model=FinancialRecordOut)
def get_record(
    record_id: int,
    _user: RequireAnalystOrAdmin,
    db: Session = Depends(get_db),
) -> FinancialRecordOut:
    rec = record_service.get_by_id(db, record_id)
    if not rec:
        raise NotFoundError("Record not found")
    return FinancialRecordOut.model_validate(rec)


@router.post("", response_model=FinancialRecordOut, status_code=201)
def create_record(
    body: FinancialRecordCreate,
    admin: RequireAdmin,
    db: Session = Depends(get_db),
) -> FinancialRecordOut:
    rec = record_service.create_record(db, body, admin)
    return FinancialRecordOut.model_validate(rec)


@router.patch("/{record_id}", response_model=FinancialRecordOut)
def update_record(
    record_id: int,
    body: FinancialRecordUpdate,
    admin: RequireAdmin,
    db: Session = Depends(get_db),
) -> FinancialRecordOut:
    rec = record_service.update_record(db, record_id, body, admin)
    return FinancialRecordOut.model_validate(rec)


@router.delete("/{record_id}", status_code=204)
def delete_record(
    record_id: int,
    admin: RequireAdmin,
    db: Session = Depends(get_db),
) -> Response:
    record_service.soft_delete_record(db, record_id, admin)
    return Response(status_code=204)
