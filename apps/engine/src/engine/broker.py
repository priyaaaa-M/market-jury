"""Paper broker with simple fee and slippage model. Supports shorts. No live orders in v1."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

SLIPPAGE_BPS = 5      # 0.05%
FEE_BPS = 3           # brokerage + STT + charges, rough average


class PaperBroker:
    def __init__(self, capital: float) -> None:
        self.initial_capital = capital
        self.capital = capital
        self.positions: dict[str, dict[str, float]] = {}
        self.trades: list[dict[str, Any]] = []

    def load(self, capital: float, positions: dict, trades: list[dict], initial: float) -> None:
        self.capital, self.positions, self.trades, self.initial_capital = (
            capital, positions, trades, initial)

    def _fill(self, action: str, price: float) -> float:
        sign = 1 if action in ("BUY", "COVER") else -1
        return round(price * (1 + sign * SLIPPAGE_BPS / 10000), 2)

    def execute(self, action: str, symbol: str, qty: int, price: float) -> dict[str, Any]:
        action = action.upper()
        if action not in ("BUY", "SELL", "SHORT", "COVER") or qty <= 0:
            raise ValueError("invalid order")
        pos = self.positions.get(symbol, {"qty": 0, "avg_price": 0.0})
        fill = self._fill(action, price)
        fees = round(fill * qty * FEE_BPS / 10000, 2)
        pnl = 0.0
        if action == "BUY":
            if fill * qty + fees > self.capital:
                raise ValueError("insufficient capital")
            total = pos["qty"] + qty
            pos["avg_price"] = (pos["avg_price"] * pos["qty"] + fill * qty) / total
            pos["qty"] = total
            self.capital -= fill * qty + fees
        elif action == "SELL":
            if pos["qty"] < qty:
                raise ValueError("not enough shares to sell")
            pnl = (fill - pos["avg_price"]) * qty - fees
            pos["qty"] -= qty
            self.capital += fill * qty - fees
        elif action == "SHORT":
            total = pos["qty"] - qty
            if pos["qty"] <= 0:
                held = -pos["qty"]
                pos["avg_price"] = (pos["avg_price"] * held + fill * qty) / (held + qty)
            pos["qty"] = total
            self.capital += fill * qty - fees
        else:  # COVER
            if pos["qty"] + qty > 0:
                raise ValueError("cover exceeds short position")
            pnl = (pos["avg_price"] - fill) * qty - fees
            pos["qty"] += qty
            self.capital -= fill * qty + fees
        if pos["qty"] == 0:
            self.positions.pop(symbol, None)
        else:
            self.positions[symbol] = pos
        trade = {"order_id": f"PAPER-{uuid.uuid4().hex[:8].upper()}",
                 "timestamp": datetime.now(timezone.utc).isoformat(), "symbol": symbol,
                 "action": action, "quantity": qty, "fill_price": fill, "fees": fees,
                 "pnl": round(pnl, 2), "capital_after": round(self.capital, 2)}
        self.trades.append(trade)
        return trade

    def summary(self, prices: dict[str, float]) -> dict[str, Any]:
        value = sum(p["qty"] * prices.get(s, p["avg_price"]) for s, p in self.positions.items())
        unreal = sum((prices.get(s, p["avg_price"]) - p["avg_price"]) * p["qty"]
                     for s, p in self.positions.items())
        realized = sum(t["pnl"] for t in self.trades)
        total_value = self.capital + value
        sells = [t for t in self.trades if t["action"] in ("SELL", "COVER")]
        wins = [t for t in sells if t["pnl"] > 0]
        return {
            "capital": round(self.capital, 2),
            "positions": {s: {"qty": int(p["qty"]), "avg_price": round(p["avg_price"], 2)}
                          for s, p in self.positions.items()},
            "positions_value": round(value, 2), "total_value": round(total_value, 2),
            "initial_capital": self.initial_capital, "realized_pnl": round(realized, 2),
            "unrealized_pnl": round(unreal, 2),
            "total_pnl": round(total_value - self.initial_capital, 2),
            "pnl_pct": round((total_value / self.initial_capital - 1) * 100, 2),
            "trades": self.trades, "total_trades": len(self.trades),
            "total_sells": len(sells),
            "win_rate": round(len(wins) / len(sells) * 100, 1) if sells else 0.0,
        }
