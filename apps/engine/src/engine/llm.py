"""LLM access with per-agent budgets. Any OpenAI-compatible endpoint works.
Without an API key, MockLLM gives deterministic placeholder arguments so the app runs offline."""
from __future__ import annotations

import json
import os
from collections import defaultdict
from typing import Any

import httpx

PRICE_PER_1K = {"default": 0.0006}  # USD per 1k tokens, rough default


class BudgetExceeded(Exception):
    pass


class CostTracker:
    def __init__(self, cfg) -> None:
        self.cfg = cfg
        self.agents: dict[str, dict[str, float]] = defaultdict(
            lambda: {"tokens": 0, "cost_usd": 0.0, "calls": 0})

    @property
    def total(self) -> float:
        return round(sum(a["cost_usd"] for a in self.agents.values()), 6)

    def check(self, agent: str) -> None:
        if self.total >= self.cfg.get("AGENT_DAILY_BUDGET_USD"):
            raise BudgetExceeded("daily budget used")
        if self.agents[agent]["cost_usd"] >= self.cfg.get("AGENT_PER_AGENT_BUDGET_USD"):
            raise BudgetExceeded(f"{agent} budget used")

    def add(self, agent: str, tokens: int, model: str = "default") -> None:
        a = self.agents[agent]
        a["tokens"] += tokens
        a["calls"] += 1
        a["cost_usd"] = round(a["cost_usd"] + tokens / 1000 * PRICE_PER_1K.get(model, 0.0006), 6)

    def report(self) -> dict[str, Any]:
        return {"daily_budget": self.cfg.get("AGENT_DAILY_BUDGET_USD"),
                "total_cost_usd": self.total,
                "agents": {k: dict(v) for k, v in self.agents.items()}}


class MockLLM:
    async def complete(self, system: str, prompt: str) -> tuple[str, int]:
        text = json.dumps({"argument": "Offline placeholder argument (no LLM key set).",
                           "evidence": ["simulated data"], "confidence": 0.5})
        return text, 50


class OpenAICompatLLM:
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.base_url, self.api_key, self.model = base_url.rstrip("/"), api_key, model

    async def complete(self, system: str, prompt: str) -> tuple[str, int]:
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": [
                    {"role": "system", "content": system}, {"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"}},
            )
            r.raise_for_status()
            body = r.json()
        return body["choices"][0]["message"]["content"], body.get("usage", {}).get("total_tokens", 0)


def llm_from_env():
    key = os.getenv("LLM_API_KEY")
    if not key:
        return MockLLM()
    return OpenAICompatLLM(os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"), key,
                           os.getenv("LLM_MODEL", "gpt-4o-mini"))
