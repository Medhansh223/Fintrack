from datetime import timedelta
from .config import (
    FRAUD_AMOUNT_THRESHOLD,
    FRAUD_BURST_TXN_COUNT,
    FRAUD_BURST_WINDOW_MINUTES,
)

def fraud_check(transactions):
    flagged = set()
    reasons_map: dict[int, list[str]] = {}

    # Rule 1: large amount
    for tx in transactions:
        if float(tx.amount) >= FRAUD_AMOUNT_THRESHOLD:
            flagged.add(tx.id)
            reasons_map.setdefault(tx.id, []).append(
                f"Large amount ≥ {int(FRAUD_AMOUNT_THRESHOLD)}"
            )

    # Rule 2: burst debits in short window
    debits = [t for t in transactions if t.txn_type == "debit"]
    debits_sorted = sorted(debits, key=lambda x: x.created_at or 0)
    k = FRAUD_BURST_TXN_COUNT
    window = timedelta(minutes=FRAUD_BURST_WINDOW_MINUTES)

    for i in range(len(debits_sorted)):
        j = i + k - 1
        if j < len(debits_sorted):
            if (debits_sorted[j].created_at - debits_sorted[i].created_at) <= window:
                for t in debits_sorted[i : j + 1]:
                    flagged.add(t.id)
                    reasons_map.setdefault(t.id, []).append(
                        f"{k}+ debits within {FRAUD_BURST_WINDOW_MINUTES} min"
                    )
    return flagged, reasons_map
