# Local run evidence - 9 October 2026

- Engine health returned 200. POST /task with type=debate, symbols=[TCS] returned accepted and task id 983ba5b56cd4.
- TCS demo verdict persisted: buy, confidence 0.64, sideways_normal_vol, two bull and two bear placeholder arguments. Paper order pending only; no execution approved.
- Dashboard at localhost:5173 connected to engine. Actual browser screenshots inspected: desktop overview, TCS debate, planner/journal, scoreboard and 390px mobile overview. Mobile overview document width 390px equals viewport, no horizontal overflow. No JavaScript errors in those tested flows.
- Browser planner request: capital=100000, risk_pct=1, entry=1000, stop=980, target=1040 returns 50 shares, planned loss=1000, reward/risk=2. Journal saved through UI and read back.
- Scoreboard: 1 logged verdict, 0 measured horizon rows, 1 demo exclusion. This is expected, not a fake performance record.
- MCP tested with an actual stdio client: handshake, 12-tool listing, then get_market_regime, get_verdict(TCS), get_scoreboard, calculate_risk_plan and get_journal calls returned without errors against the running engine. Not tested in Claude Desktop/Cursor.
- Engine: 23 tests pass. Ruff passes. TypeScript/Vite production build succeeds. Dependency changes rebuilt; React Router updated to remove production audit findings, Vite/plugin updated. Remaining Tailwind 3 toolchain advisories documented in SECURITY.md. Not production hosting approval.

No broker access, live data, paid LLM, public hosting or GitHub push. Screenshots use simulated observations and test-only journal text. Engine API secret and databases excluded from source.

## Additional live tests
- OpenRouter free-only router: one two-sided TCS debate, two generated calls; cohere/north-mini-code:free and nvidia/nemotron-3-ultra-550b-a55b:free; receipts report zero cost, account usage stayed zero. Real AI text on synthetic inputs, not a real market call. Keys saved to vault, local .env removed after test; no keys tracked.
- Data-only Yahoo run: MARKET_DATA_MODE=yahoo, no LLM key. Oct 9 bars: TCS 2156.00, RELIANCE 1170.30, INFY 1023.40, HDFCBANK 707.25, Nifty 22520.45, VIX 14.375. Same-day adjusted daily observations; not live ticks or NSE-verified official close. Fresh independent public-page evidence could not establish comparable closing agreement.
- Public cross-check UI tested with factual dated snapshots: TCS different date, Reliance different price type, both incomparable; other watchlist symbols unavailable. Comparator unit tests exercise agreement, mismatch, incomparable and unavailable. No actual two-source closing agreement obtained.

## Monochrome UI
Black/white/grays restyle verified at desktop and 390px mobile. Active navigation underline, explicit badge text and white outlines preserve status meaning without color. White BUY badge, black outlined SELL badge, gray HOLD badge. Existing wide observation table scrolls within the card; mobile swipe hint added and right-side source/check columns visually inspected. Risk-planner API flow still works. This is a visual check, not a formal accessibility audit.

Latest visual direction: light monochrome (white background/cards, dark text, gray controls). Desktop and 390px mobile inspected; risk planner request works. White BUY badge has black outline for visibility on white cards, SELL retains black fill, HOLD gray. Prior black-background screenshots are superseded by this user-directed light theme.
