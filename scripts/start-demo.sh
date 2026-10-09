#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v python3 >/dev/null || { echo 'Install Python 3.10+ first.'; exit 1; }
command -v npm >/dev/null || { echo 'Install Node.js 22.12+ first.'; exit 1; }
python3 -m venv .venv
.venv/bin/python -m pip install -e 'apps/engine[dev]' -e packages/mcp-server
(cd apps/web && npm ci)
# Demo must never consume paid API keys inherited from the caller.
unset LLM_API_KEY
export MARKET_DATA_MODE=simulated AGENT_FORCE_ACTIVE=true AGENT_AUTO_EXECUTE=false
export API_KEY="$(.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(24))')"
export DB_PATH="${DB_PATH:-demo.db}"
printf '\nOpen http://localhost:5173 and enter this LOCAL demo key: %s\nCtrl+C stops both processes. All prices/arguments are demo data.\n' "$API_KEY"
.venv/bin/python -m engine &
engine_pid=$!
trap 'kill "$engine_pid" "$web_pid" 2>/dev/null || true' EXIT INT TERM
(cd apps/web && npm run dev -- --host 127.0.0.1) &
web_pid=$!
wait -n "$engine_pid" "$web_pid"
