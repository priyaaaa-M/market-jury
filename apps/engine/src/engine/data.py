"""Explicit data provenance. Real-data failures never become synthetic observations."""
from __future__ import annotations

import hashlib
import math
import os
from datetime import date, datetime, timedelta, timezone
from typing import Protocol

DEFAULT_UNIVERSE = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "LUPIN", "SBIN", "ITC"]
class MarketData(Protocol):
    source: str
    def quote(self, symbol: str) -> dict: ...
    def history(self, symbol: str, days: int = 60) -> list[float]: ...
    def index_series(self, name: str, days: int = 60) -> list[float]: ...
    def daily_bars(self, symbol: str, start: date, end: date) -> list[dict]: ...

def _seed(*parts: str) -> int:
    return int(hashlib.sha256("|".join(parts).encode()).hexdigest()[:12], 16)

class SimulatedData:
    source = "simulated"
    BASE = {"NIFTY": 24000.0, "INDIAVIX": 14.0}
    def _price(self, symbol: str, day: date) -> float:
        # Stable across requested window lengths and restarts, unlike a moving seeded walk.
        base = self.BASE.get(symbol, 200 + _seed(symbol) % 3000)
        offset = day.toordinal() - date(2026, 1, 1).toordinal()
        phase = (_seed(symbol) % 100) / 10
        return round(base * math.exp(.0003 * offset + .06 * math.sin(offset / 12 + phase)), 2)
    def daily_bars(self, symbol: str, start: date, end: date) -> list[dict]:
        out = []
        while start <= end:
            if start.weekday() < 5:
                out.append({"date": start.isoformat(), "close": self._price(symbol, start)})
            start += timedelta(days=1)
        return out
    def history(self, symbol: str, days: int = 60) -> list[float]:
        today = datetime.now(timezone.utc).date()
        return [x["close"] for x in self.daily_bars(symbol, today-timedelta(days=days*2+10), today)][-days:]
    def index_series(self, name: str, days: int = 60) -> list[float]:
        return self.history(name, days)
    def quote(self, symbol: str) -> dict:
        h = self.history(symbol, 2)
        return {"symbol": symbol, "price": h[-1], "volume": 100000 + _seed(symbol) % 900000,
                "timestamp": datetime.now(timezone.utc).isoformat(), "exchange": "DEMO",
                "data_source": self.source, "extra": {"prev_close": h[0]}}
    def price_on(self, symbol: str, when: datetime) -> float | None:
        return self._price(symbol, when.date()) if when.date().weekday() < 5 else None

class YahooData(SimulatedData):
    """Delayed daily bars for research, not execution. Requires yfinance. No demo fallback."""
    source = "yahoo_delayed"
    def __init__(self) -> None:
        import yfinance  # noqa: F401
        self.cache = {}
    def daily_bars(self, symbol: str, start: date, end: date) -> list[dict]:
        import time

        import yfinance as yf
        ticker = {"NIFTY": "^NSEI", "INDIAVIX": "^INDIAVIX"}.get(symbol, f"{symbol}.NS")
        key = (ticker, start, end)
        if key in self.cache and time.monotonic()-self.cache[key][0] < 300:
            return self.cache[key][1]
        try:
            df = yf.Ticker(ticker).history(start=start.isoformat(), end=(end+timedelta(days=1)).isoformat(), auto_adjust=True)
            bars = [{"date": i.date().isoformat(), "close": float(r["Close"])} for i,r in df.iterrows()]
            if any(not math.isfinite(b["close"]) or b["close"] <= 0 for b in bars):
                raise ValueError("Invalid provider close")
        except Exception as e:
            raise ValueError(f"Market data unavailable for {symbol}; no simulated fallback") from e
        if not bars:
            raise ValueError(f"Market data unavailable for {symbol}; no simulated fallback")
        self.cache[key] = (time.monotonic(), bars)
        return bars
    def history(self, symbol: str, days: int = 60) -> list[float]:
        today = datetime.now(timezone.utc).date()
        return [x["close"] for x in self.daily_bars(symbol, today-timedelta(days=days*2+15), today)][-days:]
    def quote(self, symbol: str) -> dict:
        today = datetime.now(timezone.utc).date()
        bars = self.daily_bars(symbol, today-timedelta(days=15), today)
        return {"symbol": symbol, "price": bars[-1]["close"], "volume": None,
                "timestamp": bars[-1]["date"], "as_of_date": bars[-1]["date"],
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "freshness": "same_day_daily_bar" if bars[-1]["date"] == today.isoformat() else "older_daily_bar",
                "price_type": "Yahoo adjusted daily close; not exchange-verified live quote",
                "comparison_price_type": "adjusted_daily_close",
                "exchange": "NSE", "data_source": self.source,
                "extra": {"prev_close": bars[-2]["close"] if len(bars)>1 else bars[-1]["close"]}}
    def price_on(self, symbol: str, when: datetime) -> float | None:
        bars = self.daily_bars(symbol, when.date(), when.date())
        return bars[0]["close"] if bars else None

def data_from_env():
    mode = os.getenv("MARKET_DATA_MODE", "simulated")
    if mode == "simulated": return SimulatedData()
    if mode == "yahoo": return YahooData()
    if mode == "twelve_data":
        from .twelvedata import TwelveData
        return TwelveData()
    raise ValueError("MARKET_DATA_MODE must be simulated, yahoo or twelve_data")
