#!/usr/bin/env bash
# Demo, end to end: start the service, walk the main path and the five safe failures with the
# mcp-greenroom CLI, print each result, stop the service.
#
# Usage: ./scripts/demo.sh   make run's app, with the real pipeline (replayed classifier, YARA scanner)
#
# Every step states the exit code it expects. The demo fails if any step differs.
# Data lives in a temporary directory, removed at the end. No network beyond localhost.

set -uo pipefail
cd "$(dirname "$0")/.."

if [[ $# -gt 0 ]]; then
  echo "Usage: ./scripts/demo.sh (no arguments)" >&2
  exit 2
fi

port="${DEMO_PORT:-8765}"
data="$(mktemp -d)"
export MCP_GREENROOM_API="http://127.0.0.1:${port}"
export MCP_GREENROOM_DATABASE_URL="sqlite:///${data}/greenroom.db"
export MCP_GREENROOM_SNAPSHOT_PATH="${data}/last-good.json"
export MCP_GREENROOM_LOG_LEVEL="WARNING"

cli=(uv run --quiet mcp-greenroom)
samples="sample-data/servers"
failures=0
pid=""

cleanup() {
  if [[ -n "$pid" ]]; then
    kill "$pid" 2>/dev/null
    wait "$pid" 2>/dev/null
  fi
  rm -rf "$data"
}
trap cleanup EXIT

# step TITLE EXPECTED_EXIT COMMAND...: run one step, print its output, check its exit code.
step() {
  local title="$1" expected="$2"
  shift 2
  printf '\n== %s (expect exit %s)\n$ %s\n' "$title" "$expected" "$*"
  "$@"
  local code=$?
  if [[ "$code" -eq "$expected" ]]; then
    printf -- '-> exit %s, as expected\n' "$code"
  else
    printf -- '-> exit %s, expected %s: DEMO STEP FAILED\n' "$code" "$expected"
    failures=$((failures + 1))
  fi
}

# submission_id FILE TOKEN: submit and print only the submission id (the case for review).
submission_id() {
  "${cli[@]}" submit "$1" --token "$2" --json \
    | uv run --quiet python -c 'import json, sys; print(json.load(sys.stdin)["submission_id"])'
}

echo "Starting the service on port ${port} (real pipeline: replayed classifier, YARA scanner)."
uv run --quiet uvicorn mcp_greenroom.api.main:app --host 127.0.0.1 --port "$port" \
  --log-level warning &
pid=$!

for _ in $(seq 1 60); do
  "${cli[@]}" health >/dev/null 2>&1 && break
  sleep 0.5
done
if ! "${cli[@]}" health >/dev/null 2>&1; then
  echo "Error: the service did not become healthy within 30 s." >&2
  echo "  Received: no healthy answer on ${MCP_GREENROOM_API}" >&2
  echo "  Next: run 'make run' on its own and read its output." >&2
  exit 1
fi

step "Health" 0 "${cli[@]}" health

echo; echo "### Main path: a benign, read-only server is approved by policy"
step "Submit payments-readonly 1.2.0" 0 "${cli[@]}" submit "$samples/payments-readonly.json" --token dev-dana
step "It is on the registry list" 0 "${cli[@]}" list
step "A client allows it and blocks the unlisted server" 20 \
  "${cli[@]}" client-check sample-data/client-configs/amp-settings.json

echo; echo "### Safe failure 1, validation rejection: an unpinned version is refused"
step "Submit invalid-unpinned (version latest)" 20 \
  "${cli[@]}" submit "$samples/invalid-unpinned.json" --token dev-dana

echo; echo "### Safe failure 2, guarded failure: a poisoned description is rejected"
step "Submit poisoned-notes 0.3.1" 20 "${cli[@]}" submit "$samples/poisoned-notes.json" --token dev-dana

echo; echo "### Safe failure 3, abstain: no classifier recording sends it to a human"
step "Submit unrecorded-reporter 0.1.0" 10 \
  "${cli[@]}" submit "$samples/unrecorded-reporter.json" --token dev-dana

echo; echo "### Safe failure 4, separation of duties: the submitter cannot review their own case"
case_id="$(submission_id "$samples/ambiguous-exporter.json" dev-riley)"
step "Status of ambiguous-exporter 2.0.0 (submitted by riley, a reviewer)" 10 \
  "${cli[@]}" status "$case_id" --token dev-sam
step "riley reviews their own case: refused" 20 \
  "${cli[@]}" review "$case_id" --approve --note "Looks fine to me." --token dev-riley
step "sam reviews it: recorded" 0 \
  "${cli[@]}" review "$case_id" --approve --note "Egress goes to our own host only." --token dev-sam
step "The audit trail names who decided, and under which policy" 0 \
  "${cli[@]}" audit "$case_id" --token dev-sam

echo; echo "### Safe failure 5, degrade mode: the store breaks, the last-good list is served"
printf 'this is not a database' >"${data}/greenroom.db"
step "List: served from the last-good copy, with a warning" 0 "${cli[@]}" list
step "Health: not ready, registry degraded" 1 "${cli[@]}" health
step "Submit while degraded: refused, nothing approved" 1 \
  "${cli[@]}" submit "$samples/payments-readonly.json" --token dev-sam

echo
if [[ $failures -eq 0 ]]; then
  echo "Demo complete: every step gave the exit code it expected."
else
  echo "Demo FAILED: ${failures} step(s) gave an unexpected exit code." >&2
  exit 1
fi
