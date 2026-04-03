from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.financial_record import EntryType, FinancialRecord
from app.schemas.analytics import (
    InsightsSummary,
    PeriodComparison,
    TopCategoryRow,
)
from app.services import dashboard_service
from app.services.query_helpers import date_filter_clause


def compare_periods(
    db: Session,
    *,
    a_start: date,
    a_end: date,
    b_start: date,
    b_end: date,
) -> PeriodComparison:
    if a_start > a_end or b_start > b_end:
        raise AppError("Each period must have start <= end")
    pa = dashboard_service.get_period_totals(db, entry_date_from=a_start, entry_date_to=a_end)
    pb = dashboard_service.get_period_totals(db, entry_date_from=b_start, entry_date_to=b_end)
    return PeriodComparison(
        period_a_label=f"{a_start.isoformat()} — {a_end.isoformat()}",
        period_b_label=f"{b_start.isoformat()} — {b_end.isoformat()}",
        period_a=pa,
        period_b=pb,
        delta_income=pa.total_income - pb.total_income,
        delta_expense=pa.total_expense - pb.total_expense,
        delta_net=pa.net_balance - pb.net_balance,
    )


def top_categories(
    db: Session,
    *,
    entry_type: EntryType,
    limit: int = 5,
    entry_date_from: date | None = None,
    entry_date_to: date | None = None,
) -> list[TopCategoryRow]:
    clause = date_filter_clause(entry_date_from, entry_date_to)
    rows = db.execute(
        select(FinancialRecord.category, func.sum(FinancialRecord.amount))
        .where(clause, FinancialRecord.entry_type == entry_type)
        .group_by(FinancialRecord.category)
        .order_by(func.sum(FinancialRecord.amount).desc())
        .limit(limit)
    ).all()
    out: list[TopCategoryRow] = []
    for i, (cat, total) in enumerate(rows, start=1):
        out.append(
            TopCategoryRow(
                rank=i,
                category=cat,
                entry_type=entry_type,
                total=Decimal(str(total)),
            )
        )
    return out


def insights(db: Session) -> InsightsSummary:
    totals = dashboard_service.get_period_totals(db)
    clause = date_filter_clause(None, None)
    count_active = db.scalar(
        select(func.count(FinancialRecord.id)).where(clause)
    ) or 0

    top_exp = top_categories(db, entry_type=EntryType.expense, limit=1)
    top_inc = top_categories(db, entry_type=EntryType.income, limit=1)

    return InsightsSummary(
        headline_net=totals.net_balance,
        top_expense_category=top_exp[0].category if top_exp else None,
        top_expense_amount=top_exp[0].total if top_exp else None,
        top_income_category=top_inc[0].category if top_inc else None,
        top_income_amount=top_inc[0].total if top_inc else None,
        record_count_active=int(count_active),
    )
