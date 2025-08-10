# server/app/database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import make_url
from .config import DATABASE_URL

url = make_url(DATABASE_URL)
db_name = url.database
if not db_name:
    raise RuntimeError("DATABASE_URL must include a database name, e.g. .../fintrack")

# ✅ connect to guaranteed-existing schema "mysql" for bootstrap
bootstrap_url = url.set(database="mysql")

# 1) Ensure target DB exists
bootstrap_engine = create_engine(bootstrap_url, pool_pre_ping=True, future=True)
with bootstrap_engine.connect() as conn:
    # simple safety: only allow alnum + underscore
    if not db_name.replace("_", "").isalnum():
        raise RuntimeError(f"Unsafe database name: {db_name}")
    conn.execute(
        text(
            f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        )
    )
bootstrap_engine.dispose()

# 2) Normal engine bound to your DB
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
