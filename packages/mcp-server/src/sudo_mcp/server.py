"""MCP server. Analysis first: no live orders. paper_trade only queues a paper order
for human approval in the dashboard unless ENGINE_MCP_ALLOW_PAPER_EXEC=1."""
from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

BASE = os.getenv("ENGINE_URL", "http://127.0.0.1:8008")
KEY = os.getenv("ENGINE_API_KEY", "")
ALLOW_EXEC = os.getenv("ENGINE_MCP_ALLOW_PAPER_EXEC") == "1"

mcp = FastMCP("market-jury")


def _call(method: str, path: str, **kw: Any) -> Any:
    r = httpx.request(method, f"{BASE}{path}", headers={"X-API-Key": KEY}, timeout=60, **kw)
    r.raise_for_status()
    return r.json()


@mcp.tool()
def get_market_regime() -> dict:
    """Current Indian market regime (trend, volatility, suggested size multiplier)."""
    return _call("GET", "/regime")


@mcp.tool()
def get_verdict(symbol: str) -> dict:
    """Latest bull vs bear debate verdict for an NSE symbol, with arguments and regime."""
    return _call("GET", f"/consensus/{symbol.upper()}")


@mcp.tool()
def run_debate(symbols: list[str]) -> dict:
    """Start bull vs bear debates. Results arrive asynchronously: call get_verdict after."""
    return _call("POST", "/task", json={"type": "debate", "symbols": symbols})


@mcp.tool()
def get_verdict_history(symbol: str | None = None, limit: int = 50) -> dict:
    """Logged verdicts with entry price and regime."""
    params: dict[str, Any] = {"limit": limit}
    if symbol:
        params["symbol"] = symbol
    return _call("GET", "/verdicts", params=params)


@mcp.tool()
def get_scoreboard() -> dict:
    """Hit rate and excess return vs Nifty of past verdicts, by horizon and regime."""
    return _call("GET", "/scoreboard")


@mcp.tool()
def get_portfolio() -> dict:
    """Paper portfolio: positions, P&L, win rate."""
    return _call("GET", "/portfolio")


@mcp.tool()
def get_watchlist() -> dict:
    """Symbols the engine is tracking."""
    return _call("GET", "/watchlist")


@mcp.tool()
def screen(symbols: list[str]) -> dict:
    """Run the screener over symbols (async; see the timeline for results)."""
    return _call("POST", "/task", json={"type": "screen", "symbols": symbols})


@mcp.tool()
def list_pending_trades() -> dict:
    """Paper trades waiting for human approval."""
    return _call("GET", "/pending")


@mcp.tool()
def approve_paper_trade(index: int) -> dict:
    """Approve a pending PAPER trade. Disabled unless ENGINE_MCP_ALLOW_PAPER_EXEC=1."""
    if not ALLOW_EXEC:
        return {"error": "Disabled. Approve trades in the dashboard, or set ENGINE_MCP_ALLOW_PAPER_EXEC=1."}
    return _call("POST", f"/trade/approve/{index}")


@mcp.tool()
def get_journal() -> dict:
    """Private research journal. Do not share without the owner permission."""
    return _call("GET", "/journal")

@mcp.tool()
def calculate_risk_plan(capital: float, risk_pct: float, entry: float, stop: float, target: float, side: str = "long") -> dict:
    """Educational equity-only position sizing. Does not place or protect an order."""
    return _call("POST", "/risk-plan", json={"capital": capital, "risk_pct": risk_pct, "entry": entry, "stop": stop, "target": target, "side": side})

@mcp.resource("market://regime")
def regime_resource() -> str:
    return str(_call("GET", "/regime"))


@mcp.prompt()
def premarket_brief() -> str:
    return ("Call get_market_regime, then get_watchlist and get_verdict for each symbol. "
            "Summarise the regime, the strongest verdicts with their bear-case risks, and "
            "what get_scoreboard says about how reliable such verdicts have been in this regime. "
            "State clearly that this is not investment advice.")


def main() -> None:
    mcp.run(transport=os.getenv("MCP_TRANSPORT", "stdio"))


if __name__ == "__main__":
    main()
