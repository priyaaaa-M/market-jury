import json

import pytest

from engine.agents import AGENT_NAMES
from engine.llm import FREE_ROLE_MODELS, FreeOpenRouterLLM
from engine.orchestrator import Engine
from engine.store import Store


class RoleLLM:
    model = "test:free"
    last_receipt = {"cost_usd": 0, "generation_id": "test"}

    async def complete(self, system, prompt):
        assert "Regime" in prompt
        return json.dumps({"argument": "Public data only. Missing fundamentals.", "evidence": [],
                           "confidence": .55, "verdict": "buy"}), 30


async def test_four_roles_and_hard_gate():
    e = Engine(store=Store(":memory:"))
    e.four_role_team = True
    e.cfg.update({"AGENT_DEBATE_ROUNDS": 1, "AGENT_AUTO_EXECUTE": False})
    for role in FREE_ROLE_MODELS:
        e.agents[role].llm = RoleLLM()
    v = await e.debate("TCS")
    assert len(v["positions"]) == 4
    assert set(p["agent_name"] for p in v["positions"]) == set(FREE_ROLE_MODELS)
    assert v["verdict"] == "hold"
    assert v["audit"]["team"] == "four_role_ai"
    assert e.costs.total == 0 and not e.broker.trades
    assert all(p["receipt"]["cost_usd"] == 0 for p in v["positions"])


async def test_invalid_judge_no_store():
    class Bad(RoleLLM):
        async def complete(self, system, prompt):
            return '{"verdict":"invest_now","confidence":0.9}', 10
    e = Engine(store=Store(":memory:")); e.four_role_team = True
    for role in FREE_ROLE_MODELS: e.agents[role].llm = RoleLLM()
    e.agents["final_judge"].llm = Bad()
    with pytest.raises(ValueError): await e.debate("TCS")
    assert not e.store.verdicts() and not e.active_debates


def test_paid_model_rejected():
    with pytest.raises(ValueError): FreeOpenRouterLLM("unused", "openai/gpt-4o")
    assert set(FREE_ROLE_MODELS) <= set(AGENT_NAMES)

async def test_free_failure_retries_once_no_verdict(monkeypatch):
    class Failing(RoleLLM):
        calls = 0
        async def complete(self, system, prompt):
            self.calls += 1
            raise ValueError("overloaded")
    async def no_delay(_): pass
    monkeypatch.setattr("engine.orchestrator.asyncio.sleep", no_delay)
    e = Engine(store=Store(":memory:")); e.four_role_team = True
    fail = Failing(); e.agents["debater_bull"].llm = fail
    with pytest.raises(ValueError): await e.debate("TCS")
    assert fail.calls == 2 and e.debate_progress["TCS"]["state"] == "failed"
    assert not e.store.verdicts() and not e.active_debates
