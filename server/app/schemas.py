from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Literal

class TransactionCreate(BaseModel):
    date: date
    description: str = Field(min_length=1, max_length=255)
    amount: float = Field(gt=0)
    txn_type: Literal["credit", "debit"]

class TransactionOut(BaseModel):
    id: int
    date: date
    description: str
    amount: float
    txn_type: str
    created_at: datetime
    is_suspicious: bool = False
    suspicious_reasons: list[str] = []

    class Config:
        from_attributes = True

class SummaryOut(BaseModel):
    total_credit: float
    total_debit: float
    net_balance: float