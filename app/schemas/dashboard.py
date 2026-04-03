from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.models.financial_record import EntryType


class CategoryTotal(BaseModel):
    category: str
    entry_type: EntryType
    total: Decimal


class TrendPoint(BaseModel):
    period_start: date
    income: Decimal
    expense: Decimal
    net: Decimal


class RecentActivityItem(BaseModel):
    id: int
    amount: Decimal
    entry_type: EntryType
    category: str
    entry_date: date
    notes: str | None


class PeriodTotals(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    net_balance: Decimal


class DashboardSummary(BaseModel):
    totals: PeriodTotals
    category_breakdown: list[CategoryTotal]
    recent_activity: list[RecentActivityItem]
    weekly_trend: list[TrendPoint]
    monthly_trend: list[TrendPoint]
