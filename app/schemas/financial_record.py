from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.financial_record import EntryType


class FinancialRecordCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    entry_type: EntryType
    category: str = Field(min_length=1, max_length=128)
    entry_date: date
    notes: str | None = Field(default=None, max_length=4000)


class FinancialRecordUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0)
    entry_type: EntryType | None = None
    category: str | None = Field(default=None, min_length=1, max_length=128)
    entry_date: date | None = None
    notes: str | None = Field(default=None, max_length=4000)


class FinancialRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    entry_type: EntryType
    category: str
    entry_date: date
    notes: str | None
    created_by_id: int
    created_at: datetime
    updated_at: datetime | None
