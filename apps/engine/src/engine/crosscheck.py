"""Compare sourced observations, never confuse quote agreement with exchange verification."""
import math
from datetime import datetime, timezone


def compare(primary: dict, secondary: dict | None, tolerance: float = 0.05) -> dict:
    if not secondary:
        return {"status": "unavailable", "note": "No independent sourced observation available"}
    result = {"secondary": secondary, "tolerance_inr": tolerance,
              "note": "Two-source agreement is not official exchange certification."}
    if secondary.get("provider") == primary.get("data_source"):
        return {**result, "status": "incomparable", "reason": "not_independent"}
    for key in ("symbol", "exchange", "as_of_date", "comparison_price_type"):
        if primary.get(key) is None or primary.get(key) != secondary.get(key):
            return {**result, "status": "incomparable", "reason": f"different_or_missing_{key}"}
    # Evidence must be dated and cannot be an intraday snapshot compared with closing price.
    if not secondary.get("source_url") or not secondary.get("observed_at"):
        return {**result,"status":"incomparable","reason":"missing_provenance"}
    try:
        age=(datetime.now(timezone.utc)-datetime.fromisoformat(secondary["observed_at"])).total_seconds()
        if age < 0 or age > 86400:
            return {**result,"status":"incomparable","reason":"evidence_stale"}
        price=float(secondary["price"])
        if not math.isfinite(price) or price<=0: raise ValueError()
    except (ValueError,TypeError,KeyError):
        return {**result,"status":"unavailable","reason":"invalid_secondary"}
    delta=abs(float(primary["price"])-price)
    return {**result,"status":"cross_checked" if delta<=tolerance else "mismatch","difference_inr":round(delta,4)}
