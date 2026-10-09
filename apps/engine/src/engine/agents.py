"""Agents. Each has a state, can be paused, and records its own history.
Quantitative signals are computed locally; the LLM supplies the written arguments."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .llm import BudgetExceeded, CostTracker

AGENT_NAMES = ["researcher", "screener", "debater_bull", "debater_bear", "analyst", "executor_agent", "risk_reviewer", "final_judge"]


class Agent:
    def __init__(self, name: str, bus, llm, costs: CostTracker) -> None:
        self.name, self.bus, self.llm, self.costs = name, bus, llm, costs
        self.state = "idle"
        self.history: list[dict[str, Any]] = []
        self.session: dict[str, Any] = {"facts": {}, "messages": [], "message_count": 0}

    def pause(self) -> None:
        self.state = "paused"

    def resume(self) -> None:
        if self.state == "paused":
            self.state = "idle"

    def record(self, type_: str, **kw: Any) -> None:
        self.history.append({"type": type_, "agent": self.name,
                             "timestamp": datetime.now(timezone.utc).isoformat(), **kw})
        self.history = self.history[-200:]

    async def ask(self, system: str, prompt: str) -> dict[str, Any]:
        if self.state == "paused":
            raise RuntimeError(f"{self.name} is paused")
        prev, self.state = self.state, "running"
        try:
            self.costs.check(self.name)
            text, tokens = await self.llm.complete(system, prompt)
            receipt = getattr(self.llm, "last_receipt", {})
            self.costs.add(self.name, tokens, model="verified_free" if receipt.get("cost_usd") == 0 else "default")
            self.session["messages"] += [{"role": "user", "content": prompt[:500]},
                                         {"role": "assistant", "content": text[:500]}]
            self.session["messages"] = self.session["messages"][-20:]
            self.session["message_count"] += 2
            try:
                parsed = json.loads(text)
                if getattr(self.llm, "last_receipt", None):
                    if not isinstance(parsed, dict) or not isinstance(parsed.get("argument"), str) or not isinstance(parsed.get("evidence"), list) or any(not isinstance(e, str) for e in parsed["evidence"]):
                        raise ValueError("Free role returned invalid argument schema")
                    confidence = float(parsed.get("confidence"))
                    if not 0 <= confidence <= 1:
                        raise ValueError("Free role returned invalid confidence")
                    parsed["confidence"] = confidence
                return parsed
            except json.JSONDecodeError:
                if getattr(self.llm, "last_receipt", None):
                    raise ValueError("Free role returned malformed JSON; debate stopped") from None
                return {"argument": text, "evidence": [], "confidence": 0.5}
        except BudgetExceeded:
            self.state = "rate_limited"
            raise
        except Exception:
            self.state = "error"
            raise
        finally:
            if self.state == "running":
                self.state = prev if prev != "running" else "idle"


def momentum(prices: list[float]) -> float:
    """5-day vs 20-day return spread squashed to -1..1."""
    if len(prices) < 21:
        return 0.0
    r5 = prices[-1] / prices[-6] - 1
    r20 = prices[-1] / prices[-21] - 1
    return max(-1.0, min(1.0, (r5 * 0.6 + r20 * 0.4) * 10))


def volatility(prices: list[float]) -> float:
    rets = [prices[i] / prices[i - 1] - 1 for i in range(1, len(prices))]
    if not rets:
        return 0.0
    m = sum(rets) / len(rets)
    return (sum((r - m) ** 2 for r in rets) / len(rets)) ** 0.5


def judge(bull: dict, bear: dict, mom: float, regime: dict) -> dict[str, Any]:
    """Deterministic consensus: debater confidences plus the momentum signal."""
    bull_score = max(0.0, min(1.0, bull.get("confidence", 0.5) + 0.25 * max(mom, 0)))
    bear_score = max(0.0, min(1.0, bear.get("confidence", 0.5) + 0.25 * max(-mom, 0)))
    diff = bull_score - bear_score
    confidence = round(min(0.95, 0.5 + abs(diff)) , 2)
    if diff > 0.25:
        verdict = "strong_buy"
    elif diff > 0.08:
        verdict = "buy"
    elif diff < -0.25:
        verdict = "strong_sell"
    elif diff < -0.08:
        verdict = "sell"
    else:
        verdict = "hold"
    # regime gate: in stressed regimes weak convictions downgrade to hold
    if verdict != "hold" and confidence < 0.6 + regime.get("confidence_adjust", 0.0):
        verdict = "hold"
    return {"verdict": verdict, "bull_score": round(bull_score, 2),
            "bear_score": round(bear_score, 2), "confidence": confidence}
