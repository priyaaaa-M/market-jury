# API

All routes need `X-API-Key`. Read: `/status /portfolio /signals /consensus/{symbol} /pending /cost /research /quotes /config /watchlist /timeline /agents /agents/{name}/(profile|history|session) /regime /scoreboard /verdicts`.
Write: `POST /task {type: research|screen|debate|analyze, symbols}`, `POST /config`, `POST /trade/approve/{i}`, `POST /trade/reject/{i}`, `POST /positions/{symbol}/close`, `POST /agents/{name}/(pause|resume)`, watchlist `POST|PUT|DELETE`, `POST /reset?confirm=true`. Stream: `GET /ws?token=KEY`.
