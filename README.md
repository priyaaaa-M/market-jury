# market-jury

Multi-agent research and **paper-trading** copilot for Indian equities. AI agents research, screen, and argue the bull and bear case for a stock; a judge gives a verdict; you approve paper trades. Phase 2 adds a **verdict scoreboard** (how did past calls do vs Nifty?) and a **regime layer** (calmer vs stressed markets change how much conviction is needed). An **MCP server** lets Claude and other assistants use the analysis.

> Not investment advice. Paper trading only. See [DISCLAIMER.md](DISCLAIMER.md).

## Features
- Six agents: researcher, screener, bull and bear debaters, analyst, executor, plus a deterministic judge
- Live dashboard: Overview, Portfolio, Debates, Agents, Watchlist, Timeline, Scoreboard, Regime, Settings
- Manual approval or paper auto-execute; fees and slippage modelled; shorts supported
- Per-agent LLM budgets, any OpenAI-compatible provider, runs offline with placeholders
- IST market phases and weekday gating (exchange holiday calendar not yet integrated)
- API-key auth, WebSocket push, SQLite persistence
- MCP server: `get_market_regime`, `run_debate`, `get_verdict`, `get_verdict_history`, `get_scoreboard`, `get_portfolio`, `screen` and more

## Quick start (free offline demo)
```bash
./scripts/start-demo.sh
```
Python 3.10+ and Node.js 22.12+ required. Open http://localhost:5173 and enter the random LOCAL key printed by the script. No broker or LLM key is needed. All prices and arguments are demo-only; calls are excluded from measured accuracy.

See [setup and MCP instructions](docs/setup.md) for Windows/manual setup, optional delayed Yahoo bars, client configuration and privacy-safe sharing. Installing the Yahoo extra alone does NOT enable it: set `MARKET_DATA_MODE=yahoo`. Real-data failure never silently falls back to synthetic observations.

## Phase 2 additions
- Per-call provenance and regime snapshot; observed 1/5/20-session outcomes vs Nifty; demo/unknown calls excluded; holds tracked separately.
- Date-tagged manual breadth/FII/DII context with missing/stale warnings; thresholds are heuristics.
- Equity risk planner, private thesis/invalidation/review journal and JSON export.
- MCP planner/journal tools, one-command demo, absolute-path config generator, responsive/keyboard UI.
- Opt-in aggregate-only `/public/scoreboard`, off by default. This is not a hosted public app.

[Trader workflow research](docs/trader-research.md) · [API](docs/api.md) · [Remaining work](docs/roadmap.md)

## CI
A GitHub Actions workflow is in `docs/ci.yml.example`. Copy it to `.github/workflows/ci.yml` to enable lint, tests and the web build.
