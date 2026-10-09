"""Forward daily-close research outcomes. Never report demo results as real accuracy."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

HORIZONS = (1, 5, 20)
BULLISH = {"buy", "strong_buy"}
BEARISH = {"sell", "strong_sell"}

def evaluate(data, verdicts: list[dict], now: datetime | None = None) -> dict[str, Any]:
    today = (now or datetime.now(ZoneInfo("Asia/Kolkata"))).astimezone(ZoneInfo("Asia/Kolkata")).date()
    rows, outcomes = [], []
    for v in verdicts:
        audit = v.get("audit", {})
        source = audit.get("data_source", "unknown")
        # Baseline is first full session AFTER call, not a close known before the call.
        call_date = datetime.fromisoformat(v["timestamp"]).astimezone(ZoneInfo("Asia/Kolkata")).date()
        record = {"id": v.get("id"), "symbol": v["symbol"], "verdict": v["verdict"],
                  "data_source": source, "horizons": {}}
        if source == "simulated" or getattr(data, "source", "unknown") == "simulated":
            record["status"] = "demo_excluded"
        elif source == "unknown" or source != data.source:
            record["status"] = "unverified_source"
        else:
            record["status"] = "waiting"
            if call_date + timedelta(days=1) > today-timedelta(days=1):
                record["horizons"] = {h: {"status": "waiting"} for h in HORIZONS}
                outcomes.append(record)
                continue
            try:
                bars = data.daily_bars(v["symbol"], call_date+timedelta(days=1), today-timedelta(days=1))
                benchmark = {b["date"]: b["close"] for b in data.daily_bars("NIFTY", call_date+timedelta(days=1), today-timedelta(days=1))}
                # Shared observed sessions handle holidays; do not guess NSE dates.
                common = [b for b in bars if b["date"] in benchmark]
                for h in HORIZONS:
                    if len(common) <= h:
                        record["horizons"][h] = {"status": "waiting"}; continue
                    first, last = common[0], common[h]
                    raw = last["close"] / first["close"] - 1
                    bench = benchmark[last["date"]] / benchmark[first["date"]] - 1
                    sign = 1 if v["verdict"] in BULLISH else -1
                    f = {"status": "scored", "start_date": first["date"], "end_date": last["date"],
                         "start_close": first["close"], "end_close": last["close"],
                         "stock_return": raw, "benchmark_return": bench,
                         "directional_excess": (raw-bench)*sign if v["verdict"] != "hold" else None}
                    f["directional_hit"] = raw*sign > 0 if v["verdict"] != "hold" else None
                    record["horizons"][h] = f
                    if v["verdict"] != "hold":
                        rows.append({"h": h, "regime": v.get("regime", "unknown"),
                                     "confidence": v["confidence"], "hit": raw*sign > 0,
                                     "excess": (raw-bench)*sign})
                    record["status"] = "scored" if v["verdict"] != "hold" else "hold_tracked"
            except (ValueError, RuntimeError):
                record["status"] = "data_unavailable"
        outcomes.append(record)
    def agg(xs):
        return {"n": len(xs), **({"hit_rate": round(sum(r["hit"] for r in xs)/len(xs),3),
               "avg_excess_return": round(sum(r["excess"] for r in xs)/len(xs),4)} if xs else {})}
    return {"total_verdicts": len(verdicts), "scored_rows": len(rows),
            "excluded_demo": sum(o["status"] == "demo_excluded" for o in outcomes),
            "by_horizon": {h: agg([r for r in rows if r["h"]==h]) for h in HORIZONS},
            "by_regime": {g: {h: agg([r for r in rows if r["regime"]==g and r["h"]==h]) for h in HORIZONS}
                          for g in sorted({r["regime"] for r in rows})},
            "calibration": {f"{b*10}%+": agg([r for r in rows if r["h"]==5 and int(r["confidence"]*10)==b]) for b in range(10) if any(r["h"]==5 and int(r["confidence"]*10)==b for r in rows)},
            "outcomes": outcomes,
            "note": "Observed trading sessions, first full session close after call. Demo/legacy unknown data excluded. Holds tracked but not directional hits. Gross research returns, not realised P&L; confidence is a heuristic, not a probability."}
