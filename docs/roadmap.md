# Roadmap / honest status

Implemented: six-agent research/paper pipeline; persisted verdict audit provenance; source-safe outcome scoreboard; Nifty/VIX regime plus date-tagged manual breadth/FII/DII context; educational risk planner; private journal + export; local one-command demo setup; stdio MCP with planner/journal tools; opt-in public aggregate scoreboard; mobile/keyboard improvements.

Verified locally: engine health + asynchronous TCS debate persisted; web desktop/mobile screenshots; planner/journal flows; scoreboard demo exclusion; MCP protocol handshake, tools listing and five calls; engine regression tests and production web build.

Not done:
- Hosted public multi-user website, read-only demo deployment and public scoreboard UI.
- Automated licensed NSE breadth/FII/DII/news/filings, intraday charts, option chains, event/holiday calendar.
- Actual real-provider end-to-end validation and elapsed real-forward performance history.
- Immutable point-in-time data, corporate-action and revision audit, independent backtesting, fees-aware outcome modelling.
- Broker integration/CSV import, alert delivery and concentration/portfolio exposure panel.
- Claude Desktop/Cursor testing, formal accessibility/security audit, multilingual onboarding.
- Live money execution; paper-only remains enforced. Any later live route needs separate user approval, current policy review and production safeguards.

CI is still a template at docs/ci.yml.example: prior GitHub OAuth scope did not include workflow. No extra access was requested. Copying to .github/workflows/ci.yml needs appropriate GitHub authorization.
