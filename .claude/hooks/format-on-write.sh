#!/usr/bin/env bash
# PostToolUse hook for Write and Edit. Formats the one Python file that was touched.
# It never blocks: formatting is a convenience, the check script is the gate.

file="$(python3 -c 'import json, sys; print(json.load(sys.stdin).get("tool_input", {}).get("file_path", ""))' 2>/dev/null)" || exit 0

case "$file" in
  *.py) ;;
  *) exit 0 ;;
esac
[ -f "$file" ] || exit 0

root="$(git -C "$(dirname "$file")" rev-parse --show-toplevel 2>/dev/null)" || exit 0
cd "$root" || exit 0
uv run --quiet ruff format --quiet "$file" >/dev/null 2>&1
exit 0
