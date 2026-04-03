from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import RequireAnyAuthenticated
from app.core.exceptions import AppError
from app.database import get_db
from app.schemas.dashboard import (
    CategoryTotal,
    DashboardSummary,
    PeriodTotals,
    RecentActivityItem,
    TrendPoint,
)
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _validate_range(entry_date_from: date | None, entry_date_to: date | None) -> None:
    if entry_date_from is not None and entry_date_to is not None and entry_date_from > entry_date_to:
        raise AppError("entry_date_from must be on or before entry_date_to")


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    _user: RequireAnyAuthenticated,
    db: Session = Depends(get_db),
    recent_limit: int = Query(10, ge=1, le=100),
    weekly_periods: int = Query(8, ge=1, le=52),
    monthly_periods: int = Query(12, ge=1, le=120),
    entry_date_from: date | None = None,
    entry_date_to: date | None = None,
) -> DashboardSummary:
    _validate_range(entry_date_from, entry_date_to)
    return dashboard_service.build_dashboard(
        db,
        recent_limit=recent_limit,
        weekly_periods=weekly_periods,
        monthly_periods=monthly_periods,
        entry_date_from=entry_date_from,
        entry_date_to=entry_date_to,
    )


@router.get("/totals", response_model=PeriodTotals)
def dashboard_totals(
    _user: RequireAnyAuthenticated,
    db: Session = Depends(get_db),
    entry_date_from: date | None = None,
    entry_date_to: date | None = None,
) -> PeriodTotals:
    _validate_range(entry_date_from, entry_date_to)
    return dashboard_service.get_period_totals(
        db, entry_date_from=entry_date_from, entry_date_to=entry_date_to
    )


@router.get("/categories", response_model=list[CategoryTotal])
def dashboard_categories(
    _user: RequireAnyAuthenticated,
    db: Session = Depends(get_db),
    entry_date_from: date | None = None,
    entry_date_to: date | None = None,
) -> list[CategoryTotal]:
    _validate_range(entry_date_from, entry_date_to)
    return dashboard_service.get_category_breakdown(
        db, entry_date_from=entry_date_from, entry_date_to=entry_date_to
    )


@router.get("/recent", response_model=list[RecentActivityItem])
def dashboard_recent(
    _user: RequireAnyAuthenticated,
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=100),
    entry_date_from: date | None = None,
    entry_date_to: date | None = None,
) -> list[RecentActivityItem]:
    _validate_range(entry_date_from, entry_date_to)
    return dashboard_service.get_recent_activity(
        db,
        limit=limit,
        entry_date_from=entry_date_from,
        entry_date_to=entry_date_to,
    )


@router.get("/trends", response_model=list[TrendPoint])
def dashboard_trends(
    _user: RequireAnyAuthenticated,
    db: Session = Depends(get_db),
    granularity: Literal["weekly", "monthly"] = Query("monthly", description="Bucket size for trend series"),
    periods: int = Query(12, ge=1, le=120, description="Number of buckets to return"),
    entry_date_from: date | None = None,
    entry_date_to: date | None = None,
) -> list[TrendPoint]:
    _validate_range(entry_date_from, entry_date_to)
    return dashboard_service.get_trends(
        db,
        granularity=granularity,
        max_periods=periods,
        entry_date_from=entry_date_from,
        entry_date_to=entry_date_to,
    )
