from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.financial_record import EntryType, FinancialRecord
from app.services.query_helpers import date_filter_clause
from app.schemas.dashboard import (
    CategoryTotal,
    DashboardSummary,
    PeriodTotals,
    RecentActivityItem,
    TrendPoint,
)


def get_period_totals(
    db: Session,
    *,
    entry_date_from: date | None = None,
    entry_date_to: date | None = None,
) -> PeriodTotals:
    clause = date_filter_clause(entry_date_from, entry_date_to)
    inc = db.scalar(
        select(func.coalesce(func.sum(FinancialRecord.amount), 0)).where(
            clause, FinancialRecord.entry_type == EntryType.income
        )
    )
    exp = db.scalar(
        select(func.coalesce(func.sum(FinancialRecord.amount), 0)).where(
            clause, FinancialRecord.entry_type == EntryType.expense
        )
    )
    total_income = Decimal(str(inc)) if inc is not None else Decimal("0")
    total_expense = Decimal(str(exp)) if exp is not None else Decimal("0")
    return PeriodTotals(
        total_income=total_income,
        total_expense=total_expense,
        net_balance=total_income - total_expense,
    )


def get_category_breakdown(
    db: Session,
    *,
    entry_date_from: date | None = None,
    entry_date_to: date | None = None,
) -> list[CategoryTotal]:
    clause = date_filter_clause(entry_date_from, entry_date_to)
    cat_rows = db.execute(
        select(FinancialRecord.category, FinancialRecord.entry_type, func.sum(FinancialRecord.amount))
        .where(clause)
        .group_by(FinancialRecord.category, FinancialRecord.entry_type)
        .order_by(FinancialRecord.category)
    ).all()
    return [CategoryTotal(category=r[0], entry_type=r[1], total=Decimal(str(r[2]))) for r in cat_rows]


def get_recent_activity(
    db: Session,
    *,
    limit: int = 10,
    entry_date_from: date | None = None,
    entry_date_to: date | None = None,
) -> list[RecentActivityItem]:
    clause = date_filter_clause(entry_date_from, entry_date_to)
    recent_rows = db.scalars(
        select(FinancialRecord)
        .where(clause)
        .order_by(FinancialRecord.entry_date.desc(), FinancialRecord.id.desc())
        .limit(limit)
    ).all()
    return [
        RecentActivityItem(
            id=r.id,
            amount=r.amount,
            entry_type=r.entry_type,
            category=r.category,
            entry_date=r.entry_date,
            notes=r.notes,
        )
        for r in recent_rows
    ]


def get_trends(
    db: Session,
    *,
    granularity: str,
    max_periods: int,
    entry_date_from: date | None = None,
    entry_date_to: date | None = None,
) -> list[TrendPoint]:
    clause = date_filter_clause(entry_date_from, entry_date_to)
    rows = db.scalars(
        select(FinancialRecord).where(clause).order_by(FinancialRecord.entry_date)
    ).all()
    mode = "week" if granularity == "weekly" else "month"
    return _bucket_trends(rows, mode, max_periods)


def build_dashboard(
    db: Session,
    *,
    recent_limit: int = 10,
    weekly_periods: int = 8,
    monthly_periods: int = 12,
    entry_date_from: date | None = None,
    entry_date_to: date | None = None,
) -> DashboardSummary:
    totals = get_period_totals(db, entry_date_from=entry_date_from, entry_date_to=entry_date_to)
    category_breakdown = get_category_breakdown(
        db, entry_date_from=entry_date_from, entry_date_to=entry_date_to
    )
    recent_activity = get_recent_activity(
        db,
        limit=recent_limit,
        entry_date_from=entry_date_from,
        entry_date_to=entry_date_to,
    )
    all_for_trends = db.scalars(
        select(FinancialRecord)
        .where(date_filter_clause(entry_date_from, entry_date_to))
        .order_by(FinancialRecord.entry_date)
    ).all()
    weekly_trend = _bucket_trends(all_for_trends, "week", weekly_periods)
    monthly_trend = _bucket_trends(all_for_trends, "month", monthly_periods)

    return DashboardSummary(
        totals=totals,
        category_breakdown=category_breakdown,
        recent_activity=recent_activity,
        weekly_trend=weekly_trend,
        monthly_trend=monthly_trend,
    )


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _month_start(d: date) -> date:
    return date(d.year, d.month, 1)


def _bucket_trends(
    records: list[FinancialRecord],
    mode: str,
    max_periods: int,
) -> list[TrendPoint]:
    buckets: dict[date, dict[str, Decimal]] = defaultdict(
        lambda: {"income": Decimal("0"), "expense": Decimal("0")}
    )
    for r in records:
        key = _week_start(r.entry_date) if mode == "week" else _month_start(r.entry_date)
        if r.entry_type == EntryType.income:
            buckets[key]["income"] += r.amount
        else:
            buckets[key]["expense"] += r.amount

    sorted_keys = sorted(buckets.keys(), reverse=True)[:max_periods]
    sorted_keys = sorted(sorted_keys)
    out: list[TrendPoint] = []
    for k in sorted_keys:
        inc = buckets[k]["income"]
        exp = buckets[k]["expense"]
        out.append(TrendPoint(period_start=k, income=inc, expense=exp, net=inc - exp))
    return out
