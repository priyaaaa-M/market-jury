.PHONY: engine web mcp test
engine:
	cd apps/engine && pip install -e '.[dev]' && python -m engine
web:
	cd apps/web && npm install && npm run dev
mcp:
	cd packages/mcp-server && pip install -e . && engine-mcp
test:
	cd apps/engine && pytest -q
