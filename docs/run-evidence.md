# Local run evidence - 9 October 2026

- Engine health returned 200. POST /task with type=debate, symbols=[TCS] returned accepted and task id 983ba5b56cd4.
- TCS demo verdict persisted: buy, confidence 0.64, sideways_normal_vol, two bull and two bear placeholder arguments. Paper order pending only; no execution approved.
- Dashboard at localhost:5173 connected to engine. Actual browser screenshots inspected: desktop overview, TCS debate, planner/journal, scoreboard and 390px mobile overview. Mobile overview document width 390px equals viewport, no horizontal overflow. No JavaScript errors in those tested flows.
- Browser planner request: capital=100000, risk_pct=1, entry=1000, stop=980, target=1040 returns 50 shares, planned loss=1000, reward/risk=2. Journal saved through UI and read back.
- Scoreboard: 1 logged verdict, 0 measured horizon rows, 1 demo exclusion. This is expected, not a fake performance record.
- MCP tested with an actual stdio client: handshake, 12-tool listing, then get_market_regime, get_verdict(TCS), get_scoreboard, calculate_risk_plan and get_journal calls returned without errors against the running engine. Not tested in Claude Desktop/Cursor.
- Engine: 23 tests pass. Ruff passes. TypeScript/Vite production build succeeds. Dependency changes rebuilt; React Router updated to remove production audit findings, Vite/plugin updated. Remaining Tailwind 3 toolchain advisories documented in SECURITY.md. Not production hosting approval.

No broker access, live data, paid LLM, public hosting or GitHub push. Screenshots use simulated observations and test-only journal text. Engine API secret and databases excluded from source.
