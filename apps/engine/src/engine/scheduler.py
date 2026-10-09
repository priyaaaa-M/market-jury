"""IST market phases and a small NSE holiday list (extend as needed)."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))

# Verify against the official NSE holiday circular before relying on this.
NSE_HOLIDAYS: set[date] = set()

PHASES = [
    (time(9, 0), time(9, 15), "pre_market"),
    (time(9, 15), time(9, 30), "opening"),
    (time(9, 30), time(12, 0), "morning"),
    (time(12, 0), time(14, 0), "afternoon"),
    (time(14, 0), time(15, 30), "closing"),
    (time(15, 30), time(16, 0), "post_market"),
]


def is_trading_day(d: date) -> bool:
    return d.weekday() < 5 and d not in NSE_HOLIDAYS


def current_phase(now: datetime | None = None) -> str:
    now = (now or datetime.now(IST)).astimezone(IST)
    if not is_trading_day(now.date()):
        return "closed"
    for start, end, name in PHASES:
        if start <= now.time() < end:
            return name
    return "closed"


def market_open(now: datetime | None = None) -> bool:
    return current_phase(now) in ("opening", "morning", "afternoon", "closing")
