"""Market data adapters. SimulatedData is deterministic and needs no network."""
from __future__ import annotations

import hashlib
import math
import random
from datetime import datetime, timezone
from typing import Protocol

DEFAULT_UNIVERSE = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "LUPIN", "SBIN", "ITC"]


class MarketData(Protocol):
    def quote(self, symbol: str) -> dict: ...
    def history(self, symbol: str, days: int = 60) -> list[float]: ...
    def index_series(self, name: str, days: int = 60) -> list[float]: ...
    def price_on(self, symbol: str, when: datetime) -> float | None: ...


def _seed(*parts: str) -> int:
    return int(hashlib.sha256("|".join(parts).encode()).hexdigest()[:12], 16)


class SimulatedData:
    """Seeded random walks. Same symbol and day always give the same series."""

    BASE = {"NIFTY": 24000.0, "INDIAVIX": 14.0}

    def _series(self, key: str, days: int, start: float, vol: float) -> list[float]:
        today = datetime.now(timezone.utc).date().toordinal()
        rng = random.Random(_seed(key))
        px, out = start, []
        for _ in range(days + 500):
            px *= math.exp(rng.gauss(0.0003, vol))
            out.append(px)
        # shift window with the calendar so "today" moves, deterministically
        end = 400 + (today % 50)
        return out[end - days: end]

    def history(self, symbol: str, days: int = 60) -> list[float]:
        start = 200 + (_seed(symbol) % 3000)
        return [round(p, 2) for p in self._series(symbol, days, float(start), 0.015)]

    def index_series(self, name: str, days: int = 60) -> list[float]:
        vol = 0.004 if name == "NIFTY" else 0.04
        return [round(p, 2) for p in self._series(name, days, self.BASE.get(name, 100.0), vol)]

    def quote(self, symbol: str) -> dict:
        h = self.history(symbol, 2)
        return {"symbol": symbol, "price": h[-1], "volume": 100000 + _seed(symbol) % 900000,
                "timestamp": datetime.now(timezone.utc).isoformat(), "exchange": "NSE",
                "extra": {"prev_close": h[0]}}

    def price_on(self, symbol: str, when: datetime) -> float | None:
        age = (datetime.now(timezone.utc) - when).days
        if age < 0 or age > 50:
            return None
        series = self.history(symbol, age + 1)
        return series[0]


class YahooData(SimulatedData):
    """Optional: pip install 'engine[yahoo]'. Falls back to simulated data on any error."""

    def __init__(self) -> None:
        import yfinance  # noqa: F401  (import check)

    def _yf(self, ticker: str, days: int) -> list[float]:
        import yfinance as yf
        df = yf.Ticker(ticker).history(period=f"{max(days, 5)}d")
        return [float(x) for x in df["Close"].tolist()][-days:]

    def history(self, symbol: str, days: int = 60) -> list[float]:
        try:
            return self._yf(f"{symbol}.NS", days) or super().history(symbol, days)
        except Exception:
            return super().history(symbol, days)

    def index_series(self, name: str, days: int = 60) -> list[float]:
        ticker = {"NIFTY": "^NSEI", "INDIAVIX": "^INDIAVIX"}.get(name)
        try:
            return self._yf(ticker, days) if ticker else super().index_series(name, days)
        except Exception:
            return super().index_series(name, days)
