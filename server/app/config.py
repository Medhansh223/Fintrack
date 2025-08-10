import os
from dotenv import load_dotenv

# Load the .env file from the project root (server folder)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]

# Fraud params
FRAUD_AMOUNT_THRESHOLD = float(os.getenv("FRAUD_AMOUNT_THRESHOLD", "50000"))
FRAUD_BURST_WINDOW_MINUTES = int(os.getenv("FRAUD_BURST_WINDOW_MINUTES", "5"))
FRAUD_BURST_TXN_COUNT = int(os.getenv("FRAUD_BURST_TXN_COUNT", "3"))

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL env var is required")
