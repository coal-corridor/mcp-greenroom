# Thin wrappers. The scripts hold the logic.
.PHONY: verify run demo record

verify:
	./scripts/verify.sh

run:
	uv run uvicorn mcp_greenroom.api.main:app --host 127.0.0.1 --port 8000

demo:
	./scripts/demo.sh

# Live model run: network and MCP_GREENROOM_MODEL_API_KEY. Only the user starts it (/record-classifier).
record:
	uv run python -m evals.record
