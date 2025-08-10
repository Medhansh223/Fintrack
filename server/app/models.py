from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, func, Enum
from .database import Base
import enum

class TxnType(str, enum.Enum):
    credit = "credit"
    debit = "debit"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    txn_type = Column(Enum(TxnType), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)