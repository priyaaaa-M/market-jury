# Market Copilot (working title)

Multi-agent research and **paper-trading** copilot for Indian equities. AI agents research, screen, and argue the bull and bear case for a stock; a judge gives a verdict; you approve paper trades. Phase 2 adds a **verdict scoreboard** (how did past calls do vs Nifty?) and a **regime layer** (calmer vs stressed markets change how much conviction is needed). An **MCP server** lets Claude and other assistants use the analysis.

> Not investment advice. Paper trading only. See [DISCLAIMER.md](DISCLAIMER.md).

## Features
- Six agents: researcher, screener, bull and bear debaters, analyst, executor, plus a deterministic judge
- Live dashboard: Overview, Portfolio, Debates, Agents, Watchlist, Timeline, Scoreboard, Regime, Settings
- Manual approval or paper auto-execute; fees and slippage modelled; shorts supported
- Per-agent LLM budgets, any OpenAI-compatible provider, runs offline with placeholders
- IST market phases and NSE trading-day logic
- API-key auth, WebSocket push, SQLite persistence
- MCP server: `get_market_regime`, `run_debate`, `get_verdict`, `get_verdict_history`, `get_scoreboard`, `get_portfolio`, `screen` and more

## Quick start
```bash
cp .env.example .env            # set API_KEY, optionally LLM_API_KEY
make engine                     # http://127.0.0.1:8008
make web                        # http://localhost:5173 (enter your API key)
make mcp                        # stdio MCP server for Claude/Cursor
```
Outside market hours set `AGENT_FORCE_ACTIVE=true` (Settings page). Data is simulated unless you install `engine[yahoo]`.

Claude Desktop MCP config:
```json
{"mcpServers": {"market-copilot": {"command": "engine-mcp",
  "env": {"ENGINE_URL": "http://127.0.0.1:8008", "ENGINE_API_KEY": "your-key"}}}}
```

See [docs/architecture.md](docs/architecture.md), [docs/api.md](docs/api.md), [docs/roadmap.md](docs/roadmap.md). Licensed MIT.
