"""LLM access with per-agent budgets. Any OpenAI-compatible endpoint works.
Without an API key, MockLLM gives deterministic placeholder arguments so the app runs offline."""
from __future__ import annotations

import asyncio
import json
import os
from collections import defaultdict
from typing import Any

import httpx

PRICE_PER_1K = {"default": 0.0006, "verified_free": 0.0}  # USD per 1k tokens, rough default


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

# Role overrides use one OpenRouter key; paid endpoints are forbidden.
FREE_ROLE_MODELS = {
    "debater_bull": "openrouter/free",
    "debater_bear": "cohere/north-mini-code:free",
    "risk_reviewer": "openrouter/free",
    "final_judge": "nvidia/nemotron-3-super-120b-a12b:free",
}

class FreeOpenRouterLLM(OpenAICompatLLM):
    def __init__(self, api_key, model):
        if model not in FREE_ROLE_MODELS.values():
            raise ValueError("Unapproved free role model")
        super().__init__("https://openrouter.ai/api/v1", api_key, model)
        self.last_receipt = {}

    async def complete(self, system, prompt):
        self.last_receipt = {}
        return await asyncio.wait_for(self._complete_free(system, prompt), timeout=150)

    async def _complete_free(self, system, prompt):
        async with httpx.AsyncClient(timeout=120) as c:
            catalog = await c.get(self.base_url + "/models")
            catalog.raise_for_status()
            found = next((m for m in catalog.json()["data"] if m["id"] == self.model), None)
            if not found or any(float(found.get("pricing", {}).get(k, "-1")) != 0 for k in ("prompt", "completion")):
                raise ValueError("Free model unavailable or price changed; no paid fallback")
            r = await c.post(self.base_url + "/chat/completions",
                headers={"Authorization": "Bearer " + self.api_key},
                json={"model": self.model, "max_tokens": 2200, "reasoning": {"effort": "low"},
                      "provider": {"max_price": {"prompt": 0, "completion": 0}, "allow_fallbacks": False},
                      "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                      "response_format": {"type": "json_object"}})
            if r.status_code != 200:
                raise ValueError(f"Free OpenRouter model unavailable (HTTP {r.status_code}); no paid fallback")
            body = r.json()
            text = body["choices"][0]["message"].get("content")
            if not text:
                raise ValueError("Free model returned no answer")
            for delay in (2, 4, 8):
                await asyncio.sleep(delay)
                gen = await c.get(self.base_url + "/generation", params={"id": body["id"]},
                                  headers={"Authorization": "Bearer " + self.api_key})
                if gen.status_code != 404:
                    break
            gen.raise_for_status()
            receipt = gen.json()["data"]
            cost = float(receipt["total_cost"])
            if cost != 0:
                raise ValueError("Unexpected nonzero OpenRouter receipt; debate stopped")
            self.last_receipt = {"generation_id": body["id"], "requested_model": self.model,
                                 "actual_model": body.get("model"), "cost_usd": cost,
                                 "provider": receipt.get("provider_name")}
            return text, body.get("usage", {}).get("total_tokens", 0)
