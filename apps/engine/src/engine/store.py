"""SQLite persistence (stdlib only). One file, survives restarts."""
from __future__ import annotations

import json
import sqlite3
import threading
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, event TEXT, time TEXT, data TEXT);
CREATE TABLE IF NOT EXISTS trades(
  order_id TEXT PRIMARY KEY, time TEXT, symbol TEXT, action TEXT, quantity INTEGER,
  fill_price REAL, fees REAL, pnl REAL, capital_after REAL);
CREATE TABLE IF NOT EXISTS verdicts(
  id INTEGER PRIMARY KEY, time TEXT, symbol TEXT, verdict TEXT, confidence REAL,
  bull_score REAL, bear_score REAL, reasoning TEXT, entry_price REAL, regime TEXT,
  positions TEXT);
CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY, value TEXT);
"""


class Store:
    def __init__(self, path: str = ":memory:") -> None:
        self._lock = threading.Lock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        columns = {r[1] for r in self.db.execute("PRAGMA table_info(verdicts)")}
        if "audit" not in columns:
            self.db.execute("ALTER TABLE verdicts ADD COLUMN audit TEXT")
            self.db.commit()

    def _run(self, sql: str, args: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            cur = self.db.execute(sql, args)
            self.db.commit()
            return cur.fetchall()

    # key/value
    def set(self, key: str, value: Any) -> None:
        self._run("INSERT OR REPLACE INTO kv(key,value) VALUES(?,?)", (key, json.dumps(value)))

    def get(self, key: str, default: Any = None) -> Any:
        rows = self._run("SELECT value FROM kv WHERE key=?", (key,))
        return json.loads(rows[0]["value"]) if rows else default

    # events
    def add_event(self, item: dict[str, Any]) -> None:
        self._run(
            "INSERT INTO events(event,time,data) VALUES(?,?,?)",
            (item["event"], item["time"], json.dumps(item["data"])),
        )

    def events(self, event: str | None = None, since: str | None = None,
               until: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        sql, args = "SELECT event,time,data FROM events WHERE 1=1", []
        if event:
            sql += " AND event=?"; args.append(event)
        if since:
            sql += " AND time>=?"; args.append(since)
        if until:
            sql += " AND time<=?"; args.append(until)
        sql += " ORDER BY id DESC"
        if limit is not None:
            sql += " LIMIT ?"; args.append(limit)
        return [{"event": r["event"], "time": r["time"], "data": json.loads(r["data"])}
                for r in self._run(sql, tuple(args))]

    # trades
    def add_trade(self, t: dict[str, Any]) -> None:
        self._run(
            "INSERT INTO trades VALUES(?,?,?,?,?,?,?,?,?)",
            (t["order_id"], t["timestamp"], t["symbol"], t["action"], t["quantity"],
             t["fill_price"], t["fees"], t["pnl"], t["capital_after"]),
        )

    def trades(self) -> list[dict[str, Any]]:
        rows = self._run("SELECT * FROM trades ORDER BY time")
        return [{"order_id": r["order_id"], "timestamp": r["time"], "symbol": r["symbol"],
                 "action": r["action"], "quantity": r["quantity"], "fill_price": r["fill_price"],
                 "fees": r["fees"], "pnl": r["pnl"], "capital_after": r["capital_after"]}
                for r in rows]

    # verdicts
    def add_verdict(self, v: dict[str, Any]) -> int:
        self._run(
            "INSERT INTO verdicts(time,symbol,verdict,confidence,bull_score,bear_score,"
            "reasoning,entry_price,regime,positions) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (v["timestamp"], v["symbol"], v["verdict"], v["confidence"], v["bull_score"],
             v["bear_score"], v["reasoning"], v.get("entry_price"), v.get("regime"),
             json.dumps(v.get("positions", []))),
        )
        vid = self._run("SELECT last_insert_rowid() AS i")[0]["i"]
        self._run("UPDATE verdicts SET audit=? WHERE id=?", (json.dumps(v.get("audit", {})), vid))
        return vid

    def verdicts(self, symbol: str | None = None, limit: int | None = 500) -> list[dict[str, Any]]:
        sql, args = "SELECT * FROM verdicts", []
        if symbol:
            sql += " WHERE symbol=?"; args.append(symbol)
        sql += " ORDER BY id DESC"
        if limit is not None:
            sql += " LIMIT ?"; args.append(limit)
        out = []
        for r in self._run(sql, tuple(args)):
            d = dict(r)
            d["timestamp"] = d.pop("time")
            d["positions"] = json.loads(d["positions"] or "[]")
            d["audit"] = json.loads(d.get("audit") or "{}")
            out.append(d)
        return out

    def reset(self) -> None:
        for t in ("events", "trades", "verdicts", "kv"):
            self._run(f"DELETE FROM {t}")
