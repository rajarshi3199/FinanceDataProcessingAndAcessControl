"""Reusable SQLAlchemy filter fragments for financial records."""

from datetime import date

from sqlalchemy import and_

from app.models.financial_record import FinancialRecord


def active_not_deleted():
    return FinancialRecord.deleted_at.is_(None)


def date_filter_clause(
    entry_date_from: date | None,
    entry_date_to: date | None,
):
    parts = [active_not_deleted()]
    if entry_date_from is not None:
        parts.append(FinancialRecord.entry_date >= entry_date_from)
    if entry_date_to is not None:
        parts.append(FinancialRecord.entry_date <= entry_date_to)
    return and_(*parts)
