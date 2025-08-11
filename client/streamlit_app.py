import os
import io
import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from datetime import date, datetime
from dateutil import parser as dtparse
from dotenv import load_dotenv

load_dotenv()

# ---------- CONFIG ----------
DEFAULT_API_BASE = os.getenv("BACKEND_URL")

st.set_page_config(page_title="FinTrack", page_icon="💸", layout="wide")
st.title("💸 FinTrack — Streamlit Frontend")

# with st.sidebar:
#     st.subheader("Backend Settings")
#     api_base = st.text_input("FastAPI base URL", value=DEFAULT_API_BASE)
#     api_base = api_base or DEFAULT_API_BASE  # <- ensure non-empty
#     timeout = st.number_input("Request timeout (sec)", min_value=3, max_value=60, value=15)
#     st.session_state["api_base"] = api_base

def _base():
    return (st.session_state.get("api_base") or DEFAULT_API_BASE).rstrip("/")

def api_get(path: str):
    url = f"{_base()}/{path.lstrip('/')}"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def api_post(path: str, payload: dict):
    url = f"{_base()}/{path.lstrip('/')}"
    r = requests.post(url, json=payload)
    r.raise_for_status()
    return r.json()

# ---------- TABS ----------
tab_add, tab_dash, tab_export = st.tabs(["➕ Add Transaction", "📊 Dashboard", "⬇️ Export"])

# ---------- ADD ----------
with tab_add:
    st.subheader("Add a new transaction")
    with st.form("add_txn"):
        c1, c2 = st.columns(2)
        with c1:
            tx_date = st.date_input("Date", value=date.today())
            amount = st.number_input("Amount (₹)", min_value=0.01, step=0.01, format="%.2f")
        with c2:
            txn_type = st.selectbox("Type", ["credit", "debit"])
            description = st.text_input("Description", placeholder="e.g., Groceries / Salary / Rent")
        submitted = st.form_submit_button("Save")

    if submitted:
        payload = {
            "date": tx_date.isoformat(),
            "description": description.strip(),
            "amount": float(amount),
            "txn_type": txn_type
        }
        try:
            res = api_post("/transactions", payload)
            if res.get("is_suspicious"):
                st.warning("Saved, but flagged suspicious: " + ", ".join(res.get("suspicious_reasons") or []))
            else:
                st.success("Transaction saved!")
            with st.expander("API Response"):
                st.json(res)
        except requests.RequestException as e:
            st.error(f"Failed to save transaction: {e}")

# ---------- DASH ----------
with tab_dash:
    cA, cB = st.columns([2, 5])
    with cA:
        st.subheader("Summary")
        try:
            s = api_get("/summary")
            st.metric("Total Credit (₹)", f"{s['total_credit']:.2f}")
            st.metric("Total Debit (₹)", f"{s['total_debit']:.2f}")
            st.metric("Net Balance (₹)", f"{s['net_balance']:.2f}")
        except requests.RequestException as e:
            st.error(f"Failed to load summary: {e}")

        st.divider()
        st.subheader("Filters (client-side)")
        start_date = st.date_input("Start date", value=None, help="Optional filter on the table/chart")
        end_date = st.date_input("End date", value=None, help="Optional filter on the table/chart")

    with cB:
        st.subheader("Transactions")
        try:
            data = api_get("/transactions")
            df = pd.DataFrame(data)

            if not df.empty:
                # 1) Parse to pandas datetime
                for col in ["date", "created_at"]:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

                # 2) Make a pure-date column to compare with Streamlit's date objects
                df["date_only"] = df["created_at"].dt.date

                # 3) Validate range
                if start_date and end_date and start_date > end_date:
                    st.warning("Start date cannot be after end date.")
                    st.stop()

                # 4) Build inclusive mask (date-only)
                mask = pd.Series(True, index=df.index)
                if start_date:
                    mask &= df["date_only"] >= start_date
                if end_date:
                    mask &= df["date_only"] <= end_date

                fdf = df.loc[mask].copy()

                # 5) Show table
                show_cols = ["id","date","description","amount","txn_type",
                            "created_at"]
                show_cols = [c for c in show_cols if c in fdf.columns]
                if fdf.empty:
                    min_d = df["date_only"].min()
                    max_d = df["date_only"].max()
                    st.info(f"No rows in range. Available data: {min_d} → {max_d}.")
                else:
                    st.dataframe(fdf[show_cols], use_container_width=True, height=420)

                    # 6) Chart uses filtered data
                    st.subheader("Spend by Type")
                    fig = plt.figure()
                    fdf.groupby("txn_type")["amount"].sum().sort_values(ascending=False).plot(kind="bar")
                    plt.title("Total by Type")
                    plt.ylabel("Amount (₹)")
                    st.pyplot(fig)
            else:
                st.info("No transactions yet. Add your first one in the tab on the left.")
        except requests.RequestException as e:
            st.error(f"Failed to load transactions: {e}")


# ---------- EXPORT ----------
with tab_export:
    st.subheader("Export CSV")
    st.caption("Downloads a CSV from the FastAPI `/export` endpoint.")
    if st.button("Fetch CSV"):
        try:
            # The API returns CSV as file content (text/csv). We request it directly:
            url = f"{_base()}/export"
            r = requests.get(url)
            r.raise_for_status()

            # If your API returns CSV as a file response (recommended), use r.text.
            # If it returns JSON with {"filename": "...", "csv": "..."} then parse JSON.
            content_type = r.headers.get("content-type", "")
            if "text/csv" in content_type:
                csv_bytes = r.content
                filename = "transactions.csv"
            else:
                # Fallback for JSON shape { "filename": "...", "csv": "..." }
                j = r.json()
                csv_bytes = j.get("csv", "").encode("utf-8")
                filename = j.get("filename", "transactions.csv")

            st.download_button("Download CSV", data=csv_bytes, file_name=filename, mime="text/csv")
            st.success("CSV ready. Click the button above to save.")
        except requests.RequestException as e:
            st.error(f"Export failed: {e}")
