# Run it locally

Requires Python 3.10+, Node.js 22.12+ and npm. No broker or LLM account is required for the demo. Internet is needed once to install dependencies.

## One command (Linux/macOS)
From the cloned repository:
```bash
./scripts/start-demo.sh
```
Open http://localhost:5173 and enter the random local key printed in the terminal. The script creates `.venv`, installs both Python packages and web dependencies, starts both servers and stops them on Ctrl+C. It deliberately unsets inherited LLM keys, forces simulated data, permits out-of-hours demo requests and keeps paper auto-execution off. Do not treat its calls as real recommendations.

## Manual / Windows
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e 'apps/engine[dev]' -e packages/mcp-server
```
Set `API_KEY` to your own strong local secret, `MARKET_DATA_MODE=simulated`, `AGENT_FORCE_ACTIVE=true`. Start `python -m engine`. In a second terminal:
```bash
cd apps/web
npm ci
npm run dev
```
The engine reads environment variables; it does NOT automatically load a .env file. `.env.example` is a configuration reference. Docker Compose loads `.env` explicitly, but its provided service is engine-only. Never publish .env or share your local key.

## Optional delayed daily data
```bash
pip install -e 'apps/engine[yahoo]'
```
Set `MARKET_DATA_MODE=yahoo` before starting the engine. Missing data raises an error, never synthetic fallback. This uses delayed adjusted daily bars, not licensed real-time NSE execution data. Provider availability, adjustments and usage rights need review before deployment. Research still uses offline placeholder arguments unless you explicitly configure an LLM; paid LLM usage is optional and not part of the demo.

## MCP for Claude Desktop / Cursor / other stdio clients
Run the engine first. Generate a config with absolute executable paths:
```bash
python scripts/mcp-config.py
```
Copy its JSON to your client's MCP settings and replace the engine key LOCALLY. Use the same Python environment used to install `engine-mcp`; on Windows it is `.venv\Scripts\engine-mcp.exe`. Tools include verdict/history/scoreboard/regime, risk planning and journal reads. Restart the client. Paper approval is disabled by default in MCP. Never send engine keys in chat or publish client configs with secrets.

Tested: real MCP stdio handshake/list/tools calls. Not tested inside Claude Desktop or Cursor.

## Sharing with everyone
The repository is open source; anyone can clone and run their own isolated instance. This change does not deploy a public website. The authenticated API exposes private holdings/journal data; NEVER publish the whole engine, a shared API key or Vite development server to the internet.

For a future hardened self-hosted instance, `PUBLIC_SCOREBOARD=true` enables unauthenticated `GET /public/scoreboard` with aggregates only. It excludes journal, portfolio and individual outcomes. Default is off. Use HTTPS and a reverse proxy that exposes only that route to public readers, and review aggregation privacy. Enabling this does not make the entire app safe for multi-user hosting.

## Accessibility
Responsive navigation, labeled planning/context inputs, keyboard focus indicator, skip-to-content, reduced-motion support and text labels alongside color. Desktop and 390px mobile overview visually checked. This is not a WCAG audit or a claim of full multilingual accessibility.

## Independent public-source comparison
The quote panel has cross_checked / mismatch / incomparable / unavailable statuses. Agreement requires a different provider, same symbol, exchange, date and price type, recent observed evidence and price within ₹0.05. This is two-source agreement, not NSE certification or a guarantee of accuracy.

Optional `PUBLIC_CROSSCHECK_FILE` points to a JSON evidence snapshot. For the inspected Oct 9 run we used `docs/evidence/public-crosscheck-2026-10-09.json`, a fetched public-page snapshot, NOT a live second feed. TCS evidence is Oct 8, Reliance evidence is morning intraday, so both honestly show incomparable against Oct 9 adjusted closing bars. INFY/HDFCBANK have no second observation and show unavailable. Snapshot evidence ages out after 24 hours and is never silently updated. Do not use the dated example as today's feed.

NSE quote endpoint and direct Trendlyne requests returned 403; no bypass or repeated probing. Automated independent-feed integration remains open. No broker/demat connection is required or made.

## Twelve Data (optional, entitlement-dependent)
Set `TWELVE_DATA_API_KEY` locally and `TWELVE_DATA_CROSSCHECK=true` while keeping `MARKET_DATA_MODE=yahoo` to compare Yahoo adjusted daily bars against Twelve Data `adjust=all` daily bars. No broker account is used. Do not put the key in source/chat; environment/vault only. Official Basic limits are 8 credits/min and 800/day, with limited market entitlement. NSE may not be included; verify with your key. No paid upgrade is automatic.

Response cache is 5 minutes, shared across clicks; quote-panel refresh runs every 5 minutes. Original fetch time is preserved. A shared rolling 8/min budget and 800/day process-local cap limit requests. 429 / JSON code 429 establishes at least a 60-second cooldown; repeated reads during it make no request. A later refresh retries after the cooldown. Other provider/network failures have cooldowns. There is no rapid retry loop. Limits are process-local, not distributed across multiple deployments; usage outside this app shares the provider quota.

Authenticated `/market/twelve/TCS?intraday=true` returns the quote endpoint's last-quote timestamp and explicitly different `intraday_last_trade` type. `/market/twelve/TCS` returns adjusted daily close evidence. Intraday quotes do NOT cross-check Yahoo daily closes. Cached observations may be delayed/entitlement restricted; their date and source remain visible. This is not live tick execution data.

`MARKET_DATA_MODE=twelve_data` is also supported for equity prices/history, but regime Nifty/VIX explicitly stays on Yahoo since Twelve index mapping is unverified. Twelve-only Nifty scoreboard evaluation is not complete. Yahoo-primary with Twelve optional cross-check is the supported verification route.

Adapter has mocked cache, backoff, request-budget, intraday/provenance and no-key tests. Live NSE access has not been verified without a supplied key.
