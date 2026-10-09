from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from engine.agents import judge, momentum
from engine.api import create_app
from engine.broker import PaperBroker
from engine.config import Config
from engine.orchestrator import Engine
from engine.regime import classify
from engine.scheduler import IST, current_phase
from engine.store import Store


def make_engine(**cfg):
    e = Engine(store=Store(":memory:"))
    e.cfg.update({"AGENT_FORCE_ACTIVE": True, **cfg})
    return e


def test_broker_long_round_trip_and_fees():
    b = PaperBroker(100000)
    b.execute("BUY", "TCS", 10, 1000)
    t = b.execute("SELL", "TCS", 10, 1100)
    assert t["pnl"] > 0 and "TCS" not in b.positions
    assert b.summary({})["win_rate"] == 100.0


def test_broker_short_and_cover():
    b = PaperBroker(100000)
    b.execute("SHORT", "INFY", 10, 1500)
    assert b.positions["INFY"]["qty"] == -10
    t = b.execute("COVER", "INFY", 10, 1400)
    assert t["pnl"] > 0 and not b.positions


def test_broker_rejects_bad_orders():
    b = PaperBroker(1000)
    with pytest.raises(ValueError):
        b.execute("BUY", "X", 100, 1000)
    with pytest.raises(ValueError):
        b.execute("SELL", "X", 1, 10)


def test_judge_regime_gate_downgrades_weak_calls():
    bull, bear = {"confidence": 0.62}, {"confidence": 0.5}
    calm = judge(bull, bear, 0.0, {"confidence_adjust": 0.0})
    stressed = judge(bull, bear, 0.0, {"confidence_adjust": 0.3})
    assert calm["verdict"] in ("buy", "hold") and stressed["verdict"] == "hold"


def test_regime_classifier():
    up = [100 + i for i in range(60)]
    r = classify(up, [12.0] * 30)
    assert r["trend"] == "up" and r["volatility"] == "low" and r["size_multiplier"] == 1.0
    hi = classify(up, [25.0] * 30)
    assert hi["size_multiplier"] == 0.5


def test_phase_closed_on_weekend():
    sat = datetime(2026, 10, 10, 11, 0, tzinfo=IST)
    assert current_phase(sat) == "closed"
    mon = datetime(2026, 10, 12, 10, 0, tzinfo=IST)
    assert current_phase(mon) == "morning"


def test_momentum_bounds():
    assert -1 <= momentum([100 + i for i in range(40)]) <= 1


async def test_debate_logs_verdict_and_pending_trade():
    e = make_engine()
    v = await e.debate("TCS")
    assert v["verdict"] in {"strong_buy", "buy", "hold", "sell", "strong_sell"}
    assert e.store.verdicts("TCS") and v["regime"]
    assert len(v["positions"]) == 2 * e.cfg.get("AGENT_DEBATE_ROUNDS")


async def test_auto_execute_creates_trade_and_persists():
    e = make_engine(AGENT_AUTO_EXECUTE=True, AGENT_MIN_CONFIDENCE=0.0)
    e.agents["debater_bull"].llm = type("L", (), {"complete": staticmethod(
        lambda s, p: _ret('{"argument":"x","evidence":[],"confidence":0.95}'))})()
    await e.debate("SBIN")
    assert e.broker.trades and e.store.trades()


async def _ret(text):
    return text, 10


def test_api_requires_key_and_roundtrip():
    e = make_engine()
    c = TestClient(create_app(e, api_key="k"))
    assert c.get("/status").status_code == 401
    h = {"X-API-Key": "k"}
    assert c.get("/status", headers=h).json()["paper_only"] is True
    assert c.put("/watchlist/ITC", headers=h).json()["symbols"].count("ITC") == 1
    assert c.post("/config", headers=h, json={"BOGUS": 1}).status_code == 400
    assert c.post("/task", headers=h, json={"type": "nope"}).status_code == 400
    assert c.post("/reset", headers=h).status_code == 400
    assert "regime" in c.get("/regime", headers=h).json()


def test_task_blocked_when_market_closed_and_not_forced():
    e = Engine(store=Store(":memory:"))
    e.cfg.update({"AGENT_FORCE_ACTIVE": False})
    from engine import orchestrator
    orchestrator.market_open = lambda *_: False
    c = TestClient(create_app(e, api_key="k"))
    r = c.post("/task", headers={"X-API-Key": "k"}, json={"type": "research", "symbols": []})
    assert r.status_code == 409


def test_config_types():
    c = Config()
    with pytest.raises(TypeError):
        c.update({"AGENT_DEBATE_ROUNDS": "two"})
