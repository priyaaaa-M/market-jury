"""Educational equity-only planning; no execution or guaranteed stop fills."""
import math


def risk_plan(capital: float, risk_pct: float, entry: float, stop: float, target: float, side: str = "long", size_multiplier: float = 1.0) -> dict:
    if not all(math.isfinite(x) for x in (capital,risk_pct,entry,stop,target)):
        raise ValueError("Values must be finite")
    if capital <= 0 or not 0 < risk_pct <= 5 or min(entry,stop,target)<=0 or side not in ("long","short"):
        raise ValueError("Positive prices/capital, risk 0-5%, side long/short required")
    if not (stop < entry < target if side == "long" else target < entry < stop):
        raise ValueError("Long: stop < entry < target. Short: target < entry < stop")
    per_share = abs(entry-stop)
    budget = capital * risk_pct/100 * size_multiplier
    qty = min(math.floor(budget/per_share), math.floor(capital/entry))
    return {"quantity": qty, "risk_budget": round(budget,2), "planned_loss": round(qty*per_share,2),
            "notional": round(qty*entry,2), "reward_risk": round(abs(target-entry)/per_share,2),
            "size_multiplier": size_multiplier,
            "note": "Educational equity sizing, no leverage. Fees, gaps and slippage can exceed this planned loss. This does not place or protect an order."}
