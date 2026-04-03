from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import RequireAnalystOrAdmin
from app.core.exceptions import AppError
from app.database import get_db
from app.models.financial_record import EntryType
from app.schemas.analytics import InsightsSummary, PeriodComparison, TopCategoryRow
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _validate_range(entry_date_from: date | None, entry_date_to: date | None) -> None:
    if entry_date_from is not None and entry_date_to is not None and entry_date_from > entry_date_to:
        raise AppError("entry_date_from must be on or before entry_date_to")


@router.get("/insights", response_model=InsightsSummary)
def analytics_insights(
    _user: RequireAnalystOrAdmin,
    db: Session = Depends(get_db),
) -> InsightsSummary:
    return analytics_service.insights(db)


@router.get("/compare-periods", response_model=PeriodComparison)
def compare_periods(
    _user: RequireAnalystOrAdmin,
    db: Session = Depends(get_db),
    period_a_start: date = Query(..., description="Period A start (inclusive)"),
    period_a_end: date = Query(..., description="Period A end (inclusive)"),
    period_b_start: date = Query(..., description="Period B start (inclusive)"),
    period_b_end: date = Query(..., description="Period B end (inclusive)"),
) -> PeriodComparison:
    return analytics_service.compare_periods(
        db,
        a_start=period_a_start,
        a_end=period_a_end,
        b_start=period_b_start,
        b_end=period_b_end,
    )


@router.get("/top-categories", response_model=list[TopCategoryRow])
def top_categories(
    _user: RequireAnalystOrAdmin,
    db: Session = Depends(get_db),
    entry_type: EntryType = Query(..., description="Rank categories for income or expense"),
    limit: int = Query(5, ge=1, le=50),
    entry_date_from: date | None = None,
    entry_date_to: date | None = None,
) -> list[TopCategoryRow]:
    _validate_range(entry_date_from, entry_date_to)
    return analytics_service.top_categories(
        db,
        entry_type=entry_type,
        limit=limit,
        entry_date_from=entry_date_from,
        entry_date_to=entry_date_to,
    )
