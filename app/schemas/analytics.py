from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.financial_record import EntryType
from app.schemas.dashboard import PeriodTotals


class PeriodComparison(BaseModel):
    """Compare two date ranges (e.g. month vs month)."""

    period_a_label: str = Field(description="First period description")
    period_b_label: str = Field(description="Second period description")
    period_a: PeriodTotals
    period_b: PeriodTotals
    delta_income: Decimal
    delta_expense: Decimal
    delta_net: Decimal


class TopCategoryRow(BaseModel):
    rank: int
    category: str
    entry_type: EntryType
    total: Decimal


class RecordStatsSummary(BaseModel):
    """Aggregates for a filtered slice of records (analyst/admin)."""

    count: int
    total_income: Decimal
    total_expense: Decimal
    net: Decimal
    date_from: date | None = None
    date_to: date | None = None


class CategoryStatRow(BaseModel):
    category: str
    entry_type: EntryType
    entry_count: int
    total: Decimal


class InsightsSummary(BaseModel):
    """High-level narrative metrics for dashboards (analyst+)."""

    headline_net: Decimal
    top_expense_category: str | None
    top_expense_amount: Decimal | None
    top_income_category: str | None
    top_income_amount: Decimal | None
    record_count_active: int
