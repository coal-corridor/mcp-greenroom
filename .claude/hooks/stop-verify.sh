#!/usr/bin/env bash
# Stop hook. Gates the end of a turn on the checks.
# Runs the quick stage (lint and types) and, once test files exist, the test stage.
# First failure in a turn: exit 2, so Claude keeps working and gets stderr as the reason.
# If Claude stops again in the same continuation (stop_hook_active is true), the stop is
# allowed, so it can stop and ask, and the person sees a warning. CI stays the gate for merges.
# The tree to check comes from the cwd field of the hook input, so a session that
# works in a git worktree is checked there and not in the main checkout.

if [ -t 0 ]; then input="{}"; else input="$(cat)"; fi

cwd="$(printf '%s' "$input" | python3 -c 'import json, sys; print(json.load(sys.stdin).get("cwd", ""))' 2>/dev/null)"
root="$(git -C "${cwd:-.}" rev-parse --show-toplevel 2>/dev/null)" || root="${CLAUDE_PROJECT_DIR:-}"
[ -n "$root" ] || exit 0
cd "$root" || exit 0

# Nothing to enforce until the check script exists.
[ -x scripts/verify.sh ] || exit 0

stages="quick"
if [ -n "$(find tests -type f -name 'test_*.py' -print -quit 2>/dev/null)" ]; then
  stages="quick test"
fi

failed=""
out=""
for stage in $stages; do
  if ! stage_out="$(./scripts/verify.sh "$stage" 2>&1)"; then
    failed="$stage"
    out="$stage_out"
    break
  fi
done
[ -z "$failed" ] && exit 0

active="$(printf '%s' "$input" | python3 -c 'import json, sys; print(str(json.load(sys.stdin).get("stop_hook_active", False)).lower())' 2>/dev/null)"
if [ "$active" = "true" ]; then
  printf '{"systemMessage": "Turn ended with ./scripts/verify.sh %s still failing. Do not merge this state."}\n' "$failed"
  exit 0
fi

{
  echo "Stop blocked: ./scripts/verify.sh $failed fails."
  echo "Expected: lint, types and the existing tests pass before you finish."
  echo "To do: fix the first error below and run the stage again. If you cannot, say what blocks you, then stop."
  echo
  printf '%s\n' "$out" | tail -n 40
} >&2
exit 2
