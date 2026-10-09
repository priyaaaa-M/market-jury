"""Ties agents, data, broker, store and the event bus together."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from . import regime as regime_mod
from . import scoreboard
from .agents import AGENT_NAMES, Agent, judge, momentum, volatility
from .broker import PaperBroker
from .bus import EventBus
from .config import PAPER_ONLY, Config
from .data import DEFAULT_UNIVERSE, MarketData, data_from_env
from .llm import BudgetExceeded, CostTracker, llm_from_env
from .scheduler import current_phase, market_open
from .store import Store

BUY_VERDICTS = {"buy", "strong_buy"}
SELL_VERDICTS = {"sell", "strong_sell"}


class Engine:
    def __init__(self, store: Store | None = None, data: MarketData | None = None,
                 llm=None, cfg: Config | None = None) -> None:
        self.cfg = cfg or Config()
        self.store = store or Store()
        self.data = data or data_from_env()
        self.bus = EventBus()
        self.bus.subscribe(self.store.add_event)
        self.costs = CostTracker(self.cfg)
        llm = llm or llm_from_env()
        self.agents = {n: Agent(n, self.bus, llm, self.costs) for n in AGENT_NAMES}
        self.broker = PaperBroker(self.cfg.get("INITIAL_CAPITAL"))
        self.watchlist: list[str] = self.store.get("watchlist", DEFAULT_UNIVERSE[:4])
        self.research: dict[str, Any] = {}
        self.signals: dict[str, list[dict]] = {}
        self.consensus: dict[str, dict] = {}
        self.pending: list[dict] = []
        self.active_debates: set[str] = set()
        self._restore()

    # persistence
    def _restore(self) -> None:
        trades = self.store.trades()
        if trades:
            state = self.store.get("broker", {})
            self.broker.load(state.get("capital", self.broker.capital), state.get("positions", {}),
                             trades, state.get("initial", self.broker.initial_capital))
        for v in reversed(self.store.verdicts(limit=200)):
            self.consensus[v["symbol"]] = v

    def _save_broker(self) -> None:
        self.store.set("broker", {"capital": self.broker.capital, "positions": self.broker.positions,
                                  "initial": self.broker.initial_capital})

    # read models
    def prices(self) -> dict[str, float]:
        syms = set(self.broker.positions) | set(self.watchlist)
        return {s: self.data.quote(s)["price"] for s in syms}

    def status(self) -> dict[str, Any]:
        phase = current_phase()
        return {"master_state": "running" if self.active_debates else "idle", "phase": phase,
                "market_open": market_open(), "active_debates": sorted(self.active_debates),
                "paper_only": PAPER_ONLY, "data_source": self.data.source,
                "agents": {n: {"state": a.state} for n, a in self.agents.items()},
                "cost": self.costs.report()}

    def portfolio(self) -> dict[str, Any]:
        return self.broker.summary(self.prices())

    def current_regime(self) -> dict[str, Any]:
        result = regime_mod.classify(self.data.index_series("NIFTY", 60),
                                     self.data.index_series("INDIAVIX", 30),
                                     context=self.store.get("regime_context", {}), source=self.data.source)
        if self.data.source != "simulated":
            result["observations"] = {name: self.data.quote(name) for name in ("NIFTY", "INDIAVIX")}
        return result

    # pipeline steps
    def _gate(self) -> None:
        if not (market_open() or self.cfg.get("AGENT_FORCE_ACTIVE")):
            raise PermissionError("market closed; enable AGENT_FORCE_ACTIVE to run anyway")

    async def research_symbols(self, symbols: list[str]) -> None:
        a = self.agents["researcher"]
        a.state = "running"
        for s in symbols:
            hist = self.data.history(s, 30)
            self.research[s] = {"symbol": s, "last": hist[-1], "change_30d": round(hist[-1] / hist[0] - 1, 4),
                                "summary": "Price-based research only. Plug in a news/filings source in data.py.",
                                "timestamp": datetime.now(timezone.utc).isoformat()}
            a.record("research", symbol=s)
            await self.bus.emit("research", {"symbol": s})
        a.state = "idle"

    async def analyze(self, symbols: list[str]) -> None:
        a = self.agents["analyst"]
        for s in symbols:
            h = self.data.history(s, 60)
            m, vol = momentum(h), volatility(h)
            sig = {"type": "technical", "source": "momentum", "symbol": s, "value": round(m, 3),
                   "confidence": round(max(0.3, 1 - vol * 20), 2),
                   "reasoning": f"Momentum {m:+.2f}, daily vol {vol:.3f}",
                   "timestamp": datetime.now(timezone.utc).isoformat()}
            self.signals[f"signals:{s}"] = [sig]
            a.record("analysis", symbol=s, confidence=sig["confidence"])
            await self.bus.emit("analysis", {"symbol": s, "value": sig["value"]})

    async def screen(self, symbols: list[str]) -> list[str]:
        a = self.agents["screener"]
        ranked = sorted(symbols, key=lambda s: -abs(momentum(self.data.history(s, 60))))
        top = ranked[: max(1, len(ranked) // 2)]
        a.record("screen", picks=top)
        await self.bus.emit("screen", {"picks": top})
        return top

    async def debate(self, symbol: str) -> dict[str, Any]:
        self.active_debates.add(symbol)
        await self.bus.emit("debate_started", {"symbol": symbol})
        try:
            bull_a, bear_a = self.agents["debater_bull"], self.agents["debater_bear"]
            hist = self.data.history(symbol, 60)
            m = momentum(hist)
            reg = self.current_regime()
            ctx = (f"Symbol {symbol}. Momentum {m:+.2f}. Regime {reg['regime']}. "
                   f"Last price {hist[-1]}. Reply as JSON with argument, evidence[], confidence 0-1.")
            positions: list[dict] = []
            last_bull = last_bear = {"confidence": 0.5}
            for rnd in range(self.cfg.get("AGENT_DEBATE_ROUNDS")):
                last_bull = await bull_a.ask("You argue the BULL case for an Indian equity.", ctx)
                positions.append({"agent_name": "debater_bull", "stance": "bull", "round": rnd,
                                  "argument": last_bull.get("argument", ""),
                                  "confidence": last_bull.get("confidence", 0.5),
                                  "evidence": last_bull.get("evidence", []), "rebuttal_to": ""})
                last_bear = await bear_a.ask("You argue the BEAR case for an Indian equity.",
                                             ctx + " Rebut: " + str(last_bull.get("argument", ""))[:300])
                positions.append({"agent_name": "debater_bear", "stance": "bear", "round": rnd,
                                  "argument": last_bear.get("argument", ""),
                                  "confidence": last_bear.get("confidence", 0.5),
                                  "evidence": last_bear.get("evidence", []), "rebuttal_to": "debater_bull"})
            res = judge(last_bull, last_bear, m, reg)
            verdict = {"symbol": symbol, **res, "positions": positions, "regime": reg["regime"],
                       "reasoning": (f"Bull {res['bull_score']} vs bear {res['bear_score']} "
                                     f"after {self.cfg.get('AGENT_DEBATE_ROUNDS')} rounds; regime {reg['regime']}."),
                       "entry_price": hist[-1],
                       "audit": {"data_source": self.data.source, "regime_snapshot": reg,
                                 "model": getattr(bull_a.llm, "model", "offline_placeholder"),
                                 "evaluation": "first_complete_session_close_after_call"},
                       "timestamp": datetime.now(timezone.utc).isoformat()}
            self.store.add_verdict(verdict)
            self.consensus[symbol] = verdict
            self.agents["debater_bull"].record("debate", symbol=symbol, confidence=res["confidence"])
            self.agents["debater_bear"].record("debate", symbol=symbol, confidence=res["confidence"])
            await self.bus.emit("consensus", {"symbol": symbol, "verdict": res["verdict"],
                                              "confidence": res["confidence"]})
            await self._maybe_trade(symbol, verdict, reg)
            return verdict
        finally:
            self.active_debates.discard(symbol)

    async def _maybe_trade(self, symbol: str, v: dict, reg: dict) -> None:
        threshold = self.cfg.get("AGENT_MIN_CONFIDENCE") + reg.get("confidence_adjust", 0.0)
        if v["confidence"] < threshold:
            return
        if v["verdict"] in BUY_VERDICTS:
            action = "BUY"
        elif v["verdict"] in SELL_VERDICTS and symbol in self.broker.positions:
            action = "SELL"
        else:
            return
        price = self.data.quote(symbol)["price"]
        budget = self.broker.capital * 0.05 * reg.get("size_multiplier", 1.0)
        qty = int(budget // price) if action == "BUY" else int(self.broker.positions[symbol]["qty"])
        if qty <= 0:
            return
        sig = {"action": action, "symbol": symbol, "quantity": qty, "confidence": v["confidence"],
               "reasoning": v["reasoning"], "style": self.cfg.get("TRADING_MODE"),
               "signals_used": [], "metadata": {"regime": reg["regime"]}}
        if self.cfg.get("AGENT_AUTO_EXECUTE"):
            await self._execute(sig)
        else:
            self.pending.append(sig)
            await self.bus.emit("trade_pending", {"symbol": symbol, "action": action, "quantity": qty})

    async def _execute(self, sig: dict) -> dict:
        assert PAPER_ONLY
        price = self.data.quote(sig["symbol"])["price"]
        trade = self.broker.execute(sig["action"], sig["symbol"], sig["quantity"], price)
        self.store.add_trade(trade)
        self._save_broker()
        self.agents["executor_agent"].record("trade", symbol=sig["symbol"], action=sig["action"])
        await self.bus.emit("trade", trade)
        return trade

    async def approve(self, idx: int) -> dict:
        if idx < 0: raise IndexError(idx)
        sig = self.pending[idx]
        trade = await self._execute(sig)
        self.pending.pop(idx)
        return trade

    def reject(self, idx: int) -> dict:
        if idx < 0: raise IndexError(idx)
        return self.pending.pop(idx)

    async def close_position(self, symbol: str) -> dict:
        pos = self.broker.positions.get(symbol)
        if not pos:
            raise KeyError(symbol)
        action = "SELL" if pos["qty"] > 0 else "COVER"
        return await self._execute({"action": action, "symbol": symbol, "quantity": abs(int(pos["qty"]))})

    async def run_task(self, type_: str, symbols: list[str]) -> str:
        self._gate()
        task_id = uuid.uuid4().hex[:12]
        symbols = symbols or self.watchlist

        async def job() -> None:
            try:
                if type_ == "research":
                    await self.research_symbols(symbols)
                elif type_ == "screen":
                    await self.screen(symbols)
                elif type_ == "analyze":
                    await self.analyze(symbols)
                elif type_ == "debate":
                    for s in symbols:
                        await self.debate(s)
                else:
                    raise ValueError(type_)
                await self.bus.emit("task_done", {"task_id": task_id, "type": type_})
            except BudgetExceeded as e:
                await self.bus.emit("task_failed", {"task_id": task_id, "error": str(e)})
            except Exception as e:  # keep the loop alive, report via event
                await self.bus.emit("task_failed", {"task_id": task_id, "error": repr(e)})

        asyncio.create_task(job())
        return task_id

    def scoreboard(self) -> dict[str, Any]:
        return scoreboard.evaluate(self.data, self.store.verdicts(limit=None))

    def hard_reset(self) -> None:
        self.store.reset()
        self.broker = PaperBroker(self.cfg.get("INITIAL_CAPITAL"))
        self.pending.clear(); self.consensus.clear(); self.signals.clear(); self.research.clear()
