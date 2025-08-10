import io
from fastapi import FastAPI, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import pandas as pd

from .database import Base, engine, get_db
from . import schemas, crud
from .utils import fraud_check
from .config import CORS_ORIGINS

app = FastAPI(title="FinTrack API", version="1.0.0")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "server is working"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/transactions", response_model=schemas.TransactionOut)
def create_transaction(tx: schemas.TransactionCreate, db: Session = Depends(get_db)):
    row = crud.create_transaction(db, tx)
    flagged, reasons = fraud_check([row])
    out = schemas.TransactionOut.model_validate(row)
    out.is_suspicious = row.id in flagged
    out.suspicious_reasons = reasons.get(row.id, [])
    return out

@app.get("/transactions", response_model=list[schemas.TransactionOut])
def get_transactions(db: Session = Depends(get_db)):
    rows = crud.list_transactions(db)
    flagged, reasons = fraud_check(rows)
    out = []
    for r in rows:
        o = schemas.TransactionOut.model_validate(r)
        o.is_suspicious = r.id in flagged
        o.suspicious_reasons = reasons.get(r.id, [])
        out.append(o)
    return out

@app.get("/summary", response_model=schemas.SummaryOut)
def get_summary(db: Session = Depends(get_db)):
    credit, debit = crud.summary(db)
    return schemas.SummaryOut(
        total_credit=round(credit, 2),
        total_debit=round(debit, 2),
        net_balance=round(credit - debit, 2),
    )

@app.get("/export")
def export_csv(db: Session = Depends(get_db)):
    rows = crud.list_transactions(db)
    data = [{
        "id": r.id,
        "date": r.date.isoformat(),
        "description": r.description,
        "amount": float(r.amount),
        "txn_type": r.txn_type,
        "created_at": r.created_at.isoformat(),
    } for r in rows]
    
    df = pd.DataFrame(data)
    buf = io.StringIO()
    df.to_csv(buf, index=False)

    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="transactions.csv"'}
    )
