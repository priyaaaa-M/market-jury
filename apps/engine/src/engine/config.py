"""Runtime configuration. Environment sets defaults, the API can change them at runtime."""
from __future__ import annotations

import os
from typing import Any

DEFAULTS: dict[str, Any] = {
    "TRADING_MODE": "equity_intraday",  # equity_intraday | equity_delivery | fno | all
    "AGENT_FORCE_ACTIVE": False,
    "AGENT_AUTO_EXECUTE": False,
    "AGENT_DEBATE_ROUNDS": 2,
    "AGENT_DAILY_BUDGET_USD": 5.0,
    "AGENT_PER_AGENT_BUDGET_USD": 1.0,
    "AGENT_MASTER_BUDGET_USD": 1.0,
    "AGENT_MIN_CONFIDENCE": 0.6,
    "INITIAL_CAPITAL": 1_000_000.0,
}

PAPER_ONLY = True  # v1 never places live orders


class Config:
    def __init__(self) -> None:
        self.values: dict[str, Any] = dict(DEFAULTS)
        for key, default in DEFAULTS.items():
            raw = os.getenv(key)
            if raw is None:
                continue
            if isinstance(default, bool):
                self.values[key] = raw.lower() in ("1", "true", "yes")
            elif isinstance(default, int):
                self.values[key] = int(raw)
            elif isinstance(default, float):
                self.values[key] = float(raw)
            else:
                self.values[key] = raw

    def get(self, key: str) -> Any:
        return self.values[key]

    def update(self, patch: dict[str, Any]) -> dict[str, Any]:
        updates = {}
        for key, value in patch.items():
            if key not in DEFAULTS:
                raise KeyError(f"unknown config key: {key}")
            expected = type(DEFAULTS[key])
            if expected is float and isinstance(value, int) and not isinstance(value, bool):
                value = float(value)
            if not isinstance(value, expected):
                raise TypeError(f"{key} expects {expected.__name__}")
            if key in ("AGENT_DEBATE_ROUNDS",) and not 1 <= value <= 5:
                raise TypeError("Debate rounds must be 1-5")
            if key == "AGENT_MIN_CONFIDENCE" and not 0 <= value <= 1:
                raise TypeError("Confidence must be 0-1")
            if expected is float:
                import math
                if not math.isfinite(value) or value < 0:
                    raise TypeError("Numeric settings must be finite and non-negative")
            updates[key] = value
        self.values.update(updates)
        return self.values
