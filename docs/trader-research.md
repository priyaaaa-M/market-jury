# Trader workflow research - 9 October 2026

## Decision
Prioritise readable watchlists and positions, planning risk before entry, a private thesis journal, and honest outcome measurement. Keep market-jury an equity research/paper sandbox, not an options terminal or a promise of profitable signals.

## Evidence and implementation

| Evidence | What it supports | What we added / deferred |
| --- | --- | --- |
| [Zerodha Terminal Mode, 18 March 2026](https://zerodha.com/z-connect/business-updates/introducing-kite-terminal-mode) | Broker workflows combine charts, watchlists, option chains, orders, positions, calculators, calendars and notes. | Keep the existing watchlist/positions; add a risk planner + journal rather than build order execution. Charts/option chains and event feeds remain future work. |
| [Kite support documentation](https://support.zerodha.com/category/trading-and-markets/trading-faqs/terminal-mode/articles/what-is-kite-terminal-mode) | Confirms the available widgets and separate intraday/investment/scalping layouts. | Mobile and keyboard-friendly layout; clearly separate research data from execution prices. |
| [Zerodha Varsity: position sizing](https://zerodha.com/varsity/chapter/position-sizing-active-traders-part-3/) | Position sizing is a distinct discipline, not simply allocating the same money to every signal. | Educational equity calculator using user-entered stop/target and risk budget; no leverage; finite-value validation; conservative regime multiplier. This is our implementation, not a claim that the article prescribes this exact formula. |
| [NSE India VIX](https://www.nseindia.com/static/products-services/indices-indiavix-index) | VIX derives from Nifty option prices and describes expected volatility over the next 30 calendar days. | Label VIX as volatility, not market direction. Thresholds are heuristics, not a validated model. |
| [NSE FII/FPI and DII reports](https://www.nseindia.com/reports/fii-dii) | Official capital-market flow report location. Fetched page exposes report headings, not the current numeric feed. | Manual provenance/date-tagged flow and breadth inputs; no claim of automatically retrieved current values. Ignore stale inputs. |
| [IndianStockMarket discussion, 20 July 2025](https://www.reddit.com/r/IndianStockMarket/comments/1m4jltx/any_good_journaling_websites_to_track_pnl/) | One user asks for simple journaling; replies include Excel and tools. Anecdotal, with self-promotion, not representative survey evidence. | Private thesis, invalidation and review journal with JSON export. No endorsement of promoted products. |
| [FnoDiary vendor page](https://fnodiary.in/) | Vendor advertises broker syncing/imports, charts and discipline journaling. Marketing claims, not independently tested. | Supports journaling/import workflow as a product category. Broker CSV import/sync deferred, not falsely claimed. |
| [SEBI study listing, 20 August 2026](https://www.sebi.gov.in/reports-and-statistics/research/aug-2026/study-profitability-of-individual-traders-in-the-equity-derivatives-segment-fy25-fy26-_103835.html) | A current regulator study exists on individual derivatives trader profitability. Only its listing was available in the fetched page. | No invented loss-rate statistic or findings. Retain paper-only boundary and avoid derivatives execution. |

## Limits
This is desk research across broker documentation, exchange/regulator sources, vendor marketing and a community discussion, not trader interviews or proof of product demand. A full broker terminal needs licensed/appropriate data, corporate actions, an exchange calendar, fees, authentication, operational security and current compliance review. The app's confidence is heuristic, not a probability of success. Future-data evaluation needs elapsed observed sessions. A synthetic demo cannot establish trading performance.
