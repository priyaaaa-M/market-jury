# Roadmap

**Phase 1 (done in this repo):** engine with six agents, bull vs bear debate, paper broker with fees and slippage, REST + WebSocket API, API-key auth, dashboard with Overview, Portfolio, Debates, Agents, Watchlist, Timeline, Settings.

**Phase 2 (basic versions included):**
- Accountability scoreboard: every verdict is logged with entry price and regime. Forward 1/5/20-day returns vs Nifty, hit rate, calibration by confidence. Needs real data and elapsed time to mean anything.
- Regime layer: Nifty trend + India VIX level/trend today. Next inputs: market breadth, FII/DII flows, event calendar (RBI, results, expiry days).

**Phase 3:** MCP server (included, analysis-first, paper approvals stay in the dashboard).

**Next:**
- Real news/filings source for the Researcher agent.
- Real NSE data adapters and an NSE holiday calendar.
- Backtester using event replay with fees and slippage, benchmark and drawdown.
- Telegram/WhatsApp approval alerts, risk panel (concentration, beta, options exposure).
- Hosted read-only demo and public scoreboard page.
- Live execution only after checking current SEBI retail-algo requirements.
