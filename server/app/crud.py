from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Tuple
from . import models, schemas

def create_transaction(db: Session, tx: schemas.TransactionCreate) -> models.Transaction:
    row = models.Transaction(
        date=tx.date,
        description=tx.description.strip(),
        amount=tx.amount,
        txn_type=tx.txn_type,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

def list_transactions(db: Session) -> List[models.Transaction]:
    return (
        db.query(models.Transaction)
        .order_by(models.Transaction.date.desc(), models.Transaction.id.desc())
        .all()
    )

def summary(db: Session) -> Tuple[float, float]:
    credit = (
        db.query(func.coalesce(func.sum(models.Transaction.amount), 0))
        .filter(models.Transaction.txn_type == "credit")
        .scalar()
        or 0
    )
    debit = (
        db.query(func.coalesce(func.sum(models.Transaction.amount), 0))
        .filter(models.Transaction.txn_type == "debit")
        .scalar()
        or 0
    )
    return float(credit), float(debit)
