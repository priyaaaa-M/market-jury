# API

`/health` is public. All other routes need `X-API-Key`, except the opt-in aggregate `/public/scoreboard` (disabled by default). WebSocket uses `/ws?token=KEY`; the local Vite proxy routes it through `/api/ws`.

Read: `/status /portfolio /signals /consensus/{symbol} /pending /cost /research /quotes /config /watchlist /timeline /agents /agents/{name}/(profile|history|session) /regime /scoreboard /verdicts /journal`.

Write: `POST /task {type: research|screen|debate|analyze, symbols}`, `POST /config`, `POST /trade/approve/{i}`, `POST /trade/reject/{i}`, `POST /positions/{symbol}/close`, `POST /agents/{name}/(pause|resume)`, watchlist `POST|PUT|DELETE`, `POST /reset?confirm=true`.

`POST /regime/context`: `as_of` (ISO date in IST), `source` (provenance text), `breadth_pct` (0-100), `fii_net_crore`, `dii_net_crore` (nullable). Today's manual context only; stale inputs ignored. Heuristic adjustments, not predictions.

`POST /risk-plan`: `capital`, `risk_pct` (0-5, exclusive 0), `entry`, `stop`, `target`, `side` (`long`/`short`). Educational equity calculation with regime multiplier; no order execution or stop protection.

`POST /journal`: `symbol`, `thesis`, `invalidation`, optional `review`; returns an id and timestamp. `DELETE /journal/{id}` removes a private entry. Journal capped at 1000 entries; export JSON before exceeding that cap.

Scoreboard: excludes synthetic/unknown legacy/mismatched sources. Uses first fully completed observed session after the call as baseline, then 1/5/20 common stock/Nifty sessions, not calendar days. Skips today's incomplete daily close. Holds have outcomes but no directional hit. Five-session confidence bins avoid pooling unlike horizons. Includes underlying start/end closes and dates. Gross adjusted price returns are research metrics, not net trade P&L. Provider revisions are not frozen; immutable signed market datasets and revisions auditing remain future work.

Optional Twelve Data: `/market/twelve/{symbol}?intraday=true` (authenticated). Enable provider/cross-check explicitly; unavailable/limit replies return 503 with Retry-After. Intraday timestamp is the provider's last-quote timestamp, not current browser time. `/quotes` optionally includes live second-provider evidence from the cached adapter. Five-minute UI refresh and server cache; unavailable/cooldown shown honestly.
