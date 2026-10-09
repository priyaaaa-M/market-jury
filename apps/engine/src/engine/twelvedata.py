"""Twelve Data public API adapter. Cached, budgeted, explicit errors, no demo fallback."""
from __future__ import annotations

import math
import os
import threading
import time
from collections import deque
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import httpx


class DataUnavailable(ValueError):
    pass

class TwelveData:
    source = "twelve_data"
    def __init__(self, api_key: str | None = None, ttl: int = 300, transport=None, clock=time.monotonic):
        self.api_key = api_key or os.getenv("TWELVE_DATA_API_KEY", "")
        self.ttl = max(120, ttl)
        self.clock = clock
        self.client = httpx.Client(base_url="https://api.twelvedata.com", timeout=20, transport=transport)
        self.lock = threading.Lock()
        self.cache = {}
        self.requests = deque()
        self.daily_count = 0
        self.day = datetime.now(timezone.utc).date()
        self.retry_at = 0.0
        self.blocked = {}

    def _request(self, endpoint: str, params: dict) -> dict:
        key = (endpoint, tuple(sorted(params.items())))
        with self.lock:  # protects budget and coalesces concurrent identical reads
            now = self.clock()
            if key in self.cache and now < self.cache[key][0]:
                return self.cache[key][1]
            if not self.api_key:
                raise DataUnavailable("Twelve Data key missing")
            if key in self.blocked and now < self.blocked[key]:
                raise DataUnavailable("Twelve Data request unavailable; cooldown active")
            if now < self.retry_at:
                raise DataUnavailable(f"Twelve Data rate-limit cooldown; retry after {math.ceil(self.retry_at-now)} seconds")
            day = datetime.now(timezone.utc).date()
            if self.day != day:
                self.daily_count = 0; self.day = day
            while self.requests and now-self.requests[0] >= 60:
                self.requests.popleft()
            if len(self.requests) >= 8:
                self.retry_at = self.requests[0]+61
                raise DataUnavailable("Twelve Data local 8/min budget used; retry after cooldown")
            if self.daily_count >= 800:
                raise DataUnavailable("Twelve Data local 800/day budget used")
            self.requests.append(now); self.daily_count += 1
            try:
                response = self.client.get(endpoint, params=params,
                    headers={"Authorization": "apikey "+self.api_key})
                body = response.json()
            except (httpx.HTTPError, ValueError):
                self.blocked[key] = now+60
                raise DataUnavailable("Twelve Data network/response error; no synthetic fallback") from None
            code = body.get("code", response.status_code)
            if response.status_code == 429 or code == 429:
                # No blocking sleep/request loop; a later scheduled/read attempt retries after cooldown.
                try: delay = max(60, int(response.headers.get("Retry-After", "60")))
                except ValueError: delay = 60
                self.retry_at = now+delay
                raise DataUnavailable("Twelve Data rate limit; cooldown active")
            if response.status_code != 200 or body.get("status") == "error":
                self.blocked[key] = now+300
                # Do not leak provider messages which may echo credentials.
                raise DataUnavailable(f"Twelve Data unavailable (code {code}); check instrument entitlement")
            body["_fetched_at"] = datetime.now(timezone.utc).isoformat()
            self.cache[key] = (now+self.ttl, body)
            return body

    def _validate(self, meta: dict, symbol: str):
        if meta.get("symbol") != symbol or meta.get("exchange") not in ("NSE", "XNSE"):
            raise DataUnavailable("Twelve Data symbol/exchange mismatch")
        if meta.get("currency") != "INR":
            raise DataUnavailable("Twelve Data currency mismatch")

    def bars(self, symbol: str, interval: str = "1day", outputsize: int = 160) -> list[dict]:
        if symbol in ("NIFTY", "INDIAVIX"):
            raise DataUnavailable("Twelve Data index mapping not independently verified; use Yahoo regime provider")
        if interval not in ("1min", "5min", "15min", "1h", "1day"):
            raise DataUnavailable("Unsupported interval")
        body = self._request("/time_series", {"symbol": symbol, "exchange": "NSE", "interval": interval,
                             "outputsize": outputsize, "adjust": "all", "timezone": "Asia/Kolkata"})
        self._validate(body.get("meta", {}), symbol)
        out = []
        for row in body.get("values", []):
            px = float(row["close"])
            if not math.isfinite(px) or px<=0: raise DataUnavailable("Invalid Twelve Data price")
            stamp = row["datetime"]
            date.fromisoformat(stamp[:10])
            out.append({"date": stamp[:10], "datetime": stamp, "close": px, "fetched_at": body["_fetched_at"]})
        if not out: raise DataUnavailable("Twelve Data returned no bars")
        return sorted(out, key=lambda b:b["datetime"])

    def quote(self, symbol: str, intraday: bool = False) -> dict:
        if intraday:
            body = self._request("/quote", {"symbol":symbol,"exchange":"NSE"})
            self._validate(body,symbol)
            px=float(body["close"])
            fetched_at=body["_fetched_at"]
            if not math.isfinite(px) or px<=0: raise DataUnavailable("Invalid Twelve Data quote")
            stamp = datetime.fromtimestamp(int(body.get("last_quote_at") or body["timestamp"]),timezone.utc).astimezone(ZoneInfo("Asia/Kolkata"))
            price_type = "intraday_last_trade"
            day=stamp.date().isoformat();stamp=stamp.isoformat()
        else:
            row=self.bars(symbol)[-1];px=row["close"];day=row["date"];stamp=row["datetime"];fetched_at=row["fetched_at"]
            price_type = "adjusted_daily_close"
        today=datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
        return {"symbol":symbol,"exchange":"NSE","price":px,"timestamp":stamp,"as_of_date":day,
                "data_source":self.source,"provider":self.source,"comparison_price_type":price_type,
                "freshness":"same_day_observation" if day==today else "older_observation",
                "retrieved_at":fetched_at,"observed_at":fetched_at,
                "source_url":"https://twelvedata.com/exchanges/xnse",
                "source_timestamp":stamp,"refresh_seconds":self.ttl,
                "note":"Provider observation, entitlement/delay dependent; not an exchange certification."}

    def daily_bars(self, symbol: str, start: date, end: date) -> list[dict]:
        if (end-start).days > 300:
            raise DataUnavailable("Twelve Data cached window limited to 300 calendar days")
        return [b for b in self.bars(symbol,outputsize=250) if start.isoformat()<=b["date"]<=end.isoformat()]

    def history(self, symbol: str, days: int = 60) -> list[float]:
        return [b["close"] for b in self.bars(symbol)][-days:]

    def index_series(self, name: str, days: int = 60) -> list[float]:
        raise DataUnavailable("Twelve Data index entitlement/mapping not verified")
