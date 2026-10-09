"""Market regime classifier (phase 2). Uses Nifty trend and India VIX level/trend.
Event calendar, breadth and FII/DII flows are planned inputs (see docs/roadmap.md)."""
from __future__ import annotations

from typing import Any


def _sma(xs: list[float], n: int) -> float:
    xs = xs[-n:]
    return sum(xs) / len(xs)


def classify(nifty: list[float], vix: list[float], context: dict | None = None, source: str = "unknown") -> dict[str, Any]:
    if len(nifty) < 20 or len(vix) < 5:
        return {"regime": "unknown", "trend": "unknown", "volatility": "unknown",
                "confidence_adjust": 0.0, "size_multiplier": 1.0, "inputs": {}}
    from datetime import datetime
    from zoneinfo import ZoneInfo
    context = context or {}
    fresh = context.get("as_of") == datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
    breadth = context.get("breadth_pct") if fresh else None
    fii = context.get("fii_net_crore") if fresh else None
    dii = context.get("dii_net_crore") if fresh else None
    last, sma20, sma50 = nifty[-1], _sma(nifty, 20), _sma(nifty, min(50, len(nifty)))
    if last > sma20 > sma50:
        trend = "up"
    elif last < sma20 < sma50:
        trend = "down"
    else:
        trend = "sideways"
    v = vix[-1]
    vol = "high" if v >= 20 else "low" if v < 13 else "normal"
    vix_rising = vix[-1] > _sma(vix, 5) * 1.05
    regime = f"{trend}_{vol}_vol"
    # In stressed regimes demand more conviction and trade smaller.
    adjust, size = 0.0, 1.0
    if vol == "high" or vix_rising:
        adjust, size = 0.10, 0.5
    elif trend == "down":
        adjust, size = 0.05, 0.75
    if breadth is not None and breadth < 40:
        adjust, size = max(adjust, 0.1), min(size, 0.5)
    if fii is not None and dii is not None and fii + dii < 0:
        adjust, size = max(adjust, 0.05), min(size, 0.75)
    return {"data_source": source, "context_status": "manual_current" if fresh else "missing_or_stale",
            "context_source": context.get("source") if fresh else None,
            "breadth_pct": breadth, "fii_net_crore": fii, "dii_net_crore": dii,
            "missing_inputs": [k for k,v in {"breadth": breadth,"fii": fii,"dii": dii}.items() if v is None],
            "method": "Heuristic thresholds, not a validated prediction model. VIX measures volatility, not direction. Manual flows are provisional.",
            "regime": regime, "trend": trend, "volatility": vol, "vix_rising": vix_rising,
            "confidence_adjust": adjust, "size_multiplier": size,
            "inputs": {"nifty": round(last, 2), "sma20": round(sma20, 2),
                       "sma50": round(sma50, 2), "india_vix": round(v, 2)}}
