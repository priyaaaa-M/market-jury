# Architecture

```
apps/web (React)  <--HTTP + WebSocket-->  apps/engine (FastAPI)  <--HTTP-->  packages/mcp-server
                                              |
                       agents -> debate -> judge -> (approval) -> paper broker
                                              |
                              SQLite: events, trades, verdicts, kv
```

- **Engine** (`apps/engine/src/engine`): `orchestrator.py` runs the pipeline. `agents.py` holds agent state, momentum/volatility signals and the deterministic judge. `regime.py` classifies the market. `scoreboard.py` scores logged verdicts. `broker.py` is the paper broker. `data.py` has simulated data and an optional Yahoo adapter. `llm.py` talks to any OpenAI-compatible API and enforces per-agent budgets; without a key an offline placeholder is used.
- **Flow:** research -> screen -> bull and bear debate (N rounds) -> judge verdict (gated by regime) -> trade signal -> pending approval or paper auto-execute.
- **Auth:** `X-API-Key` header on HTTP, `?token=` on `/ws`.
- **Web** is a thin client. WebSocket events invalidate queries, so pages refresh without polling.
- **MCP** wraps the HTTP API. It exposes analysis tools. Trade approval over MCP is off unless `ENGINE_MCP_ALLOW_PAPER_EXEC=1`.
