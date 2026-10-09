"""HTTP + WebSocket API. Every route needs the API key (X-API-Key header or ?token= on /ws).
If API_KEY is not set, a random key is generated and printed at startup."""
from __future__ import annotations

import asyncio
import os
import secrets
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .orchestrator import Engine

TASK_TYPES = {"research", "screen", "debate", "analyze"}


class TaskIn(BaseModel):
    type: str
    symbols: list[str] = []


class RegimeContextIn(BaseModel):
    as_of: str
    source: str = Field(min_length=3, max_length=300)
    breadth_pct: float | None = Field(default=None, ge=0, le=100)
    fii_net_crore: float | None = None
    dii_net_crore: float | None = None

class RiskIn(BaseModel):
    capital: float
    risk_pct: float
    entry: float
    stop: float
    target: float
    side: str = "long"

class JournalIn(BaseModel):
    symbol: str = Field(min_length=1, max_length=30)
    thesis: str = Field(min_length=1, max_length=2000)
    invalidation: str = Field(min_length=1, max_length=1000)
    review: str = Field(default="", max_length=2000)

def create_app(engine: Engine | None = None, api_key: str | None = None) -> FastAPI:
    eng = engine or Engine(store=None)
    key = api_key or os.getenv("API_KEY") or secrets.token_urlsafe(24)
    if not (api_key or os.getenv("API_KEY")):
        print(f"[engine] API_KEY not set. Generated key for this run: {key}")
    app = FastAPI(title="Engine API", version="0.1.0")
    origins = [o for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o]
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])
    app.state.engine = eng

    def auth(x_api_key: str | None = Header(default=None)) -> None:
        if not x_api_key or not secrets.compare_digest(x_api_key, key):
            raise HTTPException(401, "invalid or missing API key")

    dep = [Depends(auth)]

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"ok": "true"}

    @app.get("/status", dependencies=dep)
    def status() -> dict[str, Any]:
        return eng.status()

    @app.get("/portfolio", dependencies=dep)
    def portfolio() -> dict[str, Any]:
        return eng.portfolio()

    @app.get("/signals", dependencies=dep)
    def signals() -> dict[str, Any]:
        return eng.signals

    @app.get("/consensus/{symbol}", dependencies=dep)
    def consensus(symbol: str) -> dict[str, Any]:
        v = eng.consensus.get(symbol.upper())
        if not v:
            raise HTTPException(404, "no verdict yet")
        return v

    @app.get("/pending", dependencies=dep)
    def pending() -> dict[str, Any]:
        return {"pending": eng.pending}

    @app.get("/cost", dependencies=dep)
    def cost() -> dict[str, Any]:
        return eng.costs.report()

    @app.get("/research", dependencies=dep)
    def research() -> dict[str, Any]:
        return eng.research

    @app.get("/quotes", dependencies=dep)
    def quotes() -> dict[str, Any]:
        from .crosscheck import compare
        evidence = eng.store.get("public_crosschecks", {})
        # Explicit optional snapshot input, never silently claim a live independent feed.
        snapshot = os.getenv("PUBLIC_CROSSCHECK_FILE")
        if snapshot:
            import json
            from pathlib import Path
            try:
                evidence = json.loads(Path(snapshot).read_text())
            except (OSError, ValueError):
                evidence = {}
        quotes = {s: eng.data.quote(s) for s in eng.watchlist}
        for symbol, q in quotes.items():
            q["crosscheck"] = compare(q, evidence.get(symbol))
        return quotes

    @app.get("/config", dependencies=dep)
    def get_config() -> dict[str, Any]:
        return eng.cfg.values

    @app.post("/config", dependencies=dep)
    def set_config(patch: dict[str, Any]) -> dict[str, Any]:
        try:
            return eng.cfg.update(patch)
        except (KeyError, TypeError) as e:
            raise HTTPException(400, str(e))

    @app.get("/watchlist", dependencies=dep)
    def get_watchlist() -> dict[str, Any]:
        return {"symbols": eng.watchlist}

    def _save_wl() -> dict[str, Any]:
        eng.store.set("watchlist", eng.watchlist)
        return {"symbols": eng.watchlist}

    @app.post("/watchlist", dependencies=dep)
    def replace_watchlist(body: dict[str, list[str]]) -> dict[str, Any]:
        eng.watchlist = [s.upper() for s in body.get("symbols", [])]
        return _save_wl()

    @app.put("/watchlist/{symbol}", dependencies=dep)
    def add_symbol(symbol: str) -> dict[str, Any]:
        s = symbol.upper()
        if s not in eng.watchlist:
            eng.watchlist.append(s)
        return _save_wl()

    @app.delete("/watchlist/{symbol}", dependencies=dep)
    def remove_symbol(symbol: str) -> dict[str, Any]:
        eng.watchlist = [s for s in eng.watchlist if s != symbol.upper()]
        return _save_wl()

    @app.get("/timeline", dependencies=dep)
    def timeline(event: str | None = None, since: str | None = None, until: str | None = None,
                 limit: int = Query(200, ge=1, le=1000)) -> dict[str, Any]:
        return {"events": eng.store.events(event, since, until, limit)}

    @app.get("/agents", dependencies=dep)
    def agents() -> dict[str, Any]:
        return {n: {"state": a.state, "profile": {"events": len(a.history),
                                                   "tokens": eng.costs.agents[n]["tokens"]}}
                for n, a in eng.agents.items()}

    def _agent(name: str):
        if name not in eng.agents:
            raise HTTPException(404, "unknown agent")
        return eng.agents[name]

    @app.get("/agents/{name}/profile", dependencies=dep)
    def agent_profile(name: str) -> dict[str, Any]:
        a = _agent(name)
        return {"state": a.state, "events": len(a.history), **eng.costs.agents[name]}

    @app.get("/agents/{name}/history", dependencies=dep)
    def agent_history(name: str) -> dict[str, Any]:
        return {"history": _agent(name).history}

    @app.get("/agents/{name}/session", dependencies=dep)
    def agent_session(name: str) -> dict[str, Any]:
        return _agent(name).session

    @app.post("/agents/{name}/pause", dependencies=dep)
    def pause(name: str) -> dict[str, str]:
        _agent(name).pause(); return {"state": "paused"}

    @app.post("/agents/{name}/resume", dependencies=dep)
    def resume(name: str) -> dict[str, str]:
        _agent(name).resume(); return {"state": _agent(name).state}

    @app.post("/task", dependencies=dep)
    async def task(body: TaskIn) -> dict[str, str]:
        if body.type not in TASK_TYPES:
            raise HTTPException(400, f"type must be one of {sorted(TASK_TYPES)}")
        try:
            tid = await eng.run_task(body.type, [s.upper() for s in body.symbols])
        except PermissionError as e:
            raise HTTPException(409, str(e))
        return {"status": "accepted", "task_id": tid}

    @app.post("/trade/approve/{idx}", dependencies=dep)
    async def approve(idx: int) -> dict[str, Any]:
        try:
            return await eng.approve(idx)
        except IndexError:
            raise HTTPException(404, "no such pending trade")
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.post("/trade/reject/{idx}", dependencies=dep)
    def reject(idx: int) -> dict[str, Any]:
        try:
            return eng.reject(idx)
        except IndexError:
            raise HTTPException(404, "no such pending trade")

    @app.post("/positions/{symbol}/close", dependencies=dep)
    async def close(symbol: str) -> dict[str, Any]:
        try:
            return await eng.close_position(symbol.upper())
        except KeyError:
            raise HTTPException(404, "no open position")

    @app.post("/reset", dependencies=dep)
    def reset(confirm: bool = False) -> dict[str, str]:
        if not confirm:
            raise HTTPException(400, "pass ?confirm=true")
        eng.hard_reset(); return {"status": "reset"}

    # phase 2
    @app.get("/regime", dependencies=dep)
    def regime() -> dict[str, Any]:
        return eng.current_regime()

    @app.get("/scoreboard", dependencies=dep)
    def scoreboard() -> dict[str, Any]:
        return eng.scoreboard()

    @app.get("/verdicts", dependencies=dep)
    def verdicts(symbol: str | None = None, limit: int = Query(100, ge=1, le=1000)) -> dict[str, Any]:
        return {"verdicts": eng.store.verdicts(symbol.upper() if symbol else None, limit)}

    @app.post("/regime/context", dependencies=dep)
    def set_regime_context(body: RegimeContextIn):
        from datetime import date, datetime
        from zoneinfo import ZoneInfo
        try:
            day = date.fromisoformat(body.as_of)
            if day > datetime.now(ZoneInfo("Asia/Kolkata")).date(): raise ValueError("Future dates are not allowed")
        except ValueError as e:
            raise HTTPException(400, str(e))
        eng.store.set("regime_context", body.model_dump())
        return eng.current_regime()

    @app.post("/risk-plan", dependencies=dep)
    def plan(body: RiskIn):
        from .workflow import risk_plan
        try:
            return risk_plan(**body.model_dump(), size_multiplier=eng.current_regime()["size_multiplier"])
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/journal", dependencies=dep)
    def journal():
        return {"entries": eng.store.get("journal", [])}

    @app.post("/journal", dependencies=dep)
    def journal_add(body: JournalIn):
        import uuid
        from datetime import datetime, timezone
        entries = eng.store.get("journal", [])
        entry = {**body.model_dump(), "symbol": body.symbol.upper(),
                 "id": uuid.uuid4().hex, "timestamp": datetime.now(timezone.utc).isoformat()}
        entries.insert(0, entry)
        eng.store.set("journal", entries[:1000])
        return entry

    @app.delete("/journal/{entry_id}", dependencies=dep)
    def journal_delete(entry_id: str):
        entries = eng.store.get("journal", [])
        eng.store.set("journal", [e for e in entries if e["id"] != entry_id])
        return {"ok": True}

    @app.get("/public/scoreboard")
    def public_scoreboard():
        # Opt-in, read-only aggregate export. Never expose account, journal or holdings.
        if os.getenv("PUBLIC_SCOREBOARD") != "true":
            raise HTTPException(404, "Public scoreboard disabled")
        result = eng.scoreboard()
        return {k: v for k,v in result.items() if k != "outcomes"}

    @app.websocket("/ws")
    async def ws(sock: WebSocket, token: str = "") -> None:
        if not secrets.compare_digest(token, key):
            await sock.close(code=4401)
            return
        await sock.accept()
        q = eng.bus.listen()
        try:
            while True:
                await sock.send_json(await q.get())
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass
        finally:
            eng.bus.unlisten(q)

    return app
