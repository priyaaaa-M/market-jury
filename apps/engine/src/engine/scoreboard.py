"""Verdict accountability (phase 2). Forward returns vs Nifty for every logged verdict."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

HORIZONS = (1, 5, 20)
BULLISH = {"buy", "strong_buy"}
BEARISH = {"sell", "strong_sell"}


def _forward(data, v: dict, horizon: int) -> dict[str, float] | None:
    when = datetime.fromisoformat(v["timestamp"])
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    age = (datetime.now(timezone.utc) - when).days
    if age < horizon or not v.get("entry_price"):
        return None
    later = data.price_on(v["symbol"], datetime.fromtimestamp(
        when.timestamp() + horizon * 86400, tz=timezone.utc))
    if later is None:
        return None
    ret = later / v["entry_price"] - 1
    n0 = data.price_on("NIFTY", when)
    n1 = data.price_on("NIFTY", datetime.fromtimestamp(when.timestamp() + horizon * 86400, tz=timezone.utc))
    bench = (n1 / n0 - 1) if n0 and n1 else 0.0
    return {"ret": ret, "excess": ret - bench}


def evaluate(data, verdicts: list[dict]) -> dict[str, Any]:
    """Return hit rates and average excess return by horizon, verdict, agent-set and regime."""
    rows = []
    for v in verdicts:
        if v["verdict"] == "hold":
            continue
        sign = 1 if v["verdict"] in BULLISH else -1
        for h in HORIZONS:
            f = _forward(data, v, h)
            if f:
                rows.append({"h": h, "regime": v.get("regime") or "unknown",
                             "verdict": v["verdict"], "conf": v["confidence"],
                             "hit": f["ret"] * sign > 0, "excess": f["excess"] * sign})

    def agg(sel) -> dict[str, Any]:
        xs = [r for r in rows if sel(r)]
        if not xs:
            return {"n": 0}
        return {"n": len(xs), "hit_rate": round(sum(r["hit"] for r in xs) / len(xs), 3),
                "avg_excess_return": round(sum(r["excess"] for r in xs) / len(xs), 4)}

    by_h = {h: agg(lambda r, h=h: r["h"] == h) for h in HORIZONS}
    regimes = sorted({r["regime"] for r in rows})
    by_regime = {g: {h: agg(lambda r, g=g, h=h: r["regime"] == g and r["h"] == h)
                     for h in HORIZONS} for g in regimes}
    buckets: dict[str, list] = defaultdict(list)
    for r in rows:
        buckets[f"{int(r['conf'] * 10) * 10}%+"].append(r)
    calibration = {k: {"n": len(x), "hit_rate": round(sum(r["hit"] for r in x) / len(x), 3)}
                   for k, x in sorted(buckets.items())}
    return {"total_verdicts": len(verdicts), "scored_rows": len(rows), "by_horizon": by_h,
            "by_regime": by_regime, "calibration": calibration,
            "note": "Forward returns need elapsed days. Simulated data is for demos only."}
