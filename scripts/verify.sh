#!/usr/bin/env bash
# The one check command. Same script locally and in CI.
#
#   ./scripts/verify.sh            all stages: lint, types, test, eval
#   ./scripts/verify.sh quick      lint and types
#   ./scripts/verify.sh <stage>    one stage: lint, types, test or eval
#
# Every requested stage runs, even after a failure. One summary table at the end.
# Exit code is non-zero if any stage failed. No network, no credentials.
#
# The eval stage is skipped, and says so, until an evaluation set exists
# (anything matching evals/dataset*). From then on it is a gate.

set -uo pipefail

cd "$(dirname "$0")/.." || exit 2

usage() {
  echo "usage: ./scripts/verify.sh [quick|lint|types|test|eval]" >&2
}

case "${1:-all}" in
  all) stages=(lint types test eval) ;;
  quick) stages=(lint types) ;;
  lint | types | test | eval) stages=("$1") ;;
  -h | --help) usage; exit 0 ;;
  *)
    echo "verify: unknown stage '$1'." >&2
    usage
    exit 2
    ;;
esac
[ $# -le 1 ] || { echo "verify: takes at most one stage, got $#." >&2; usage; exit 2; }

if ! command -v uv >/dev/null 2>&1; then
  echo "verify: uv not found on PATH. Install uv (https://docs.astral.sh/uv/), then run 'uv sync'." >&2
  exit 2
fi

# --locked: a lockfile out of step with pyproject.toml is a failure, not a silent re-resolve.
run() { uv run --locked "$@"; }

now() { printf '%s' "${EPOCHREALTIME:-$SECONDS}"; }
elapsed() { awk -v a="$1" -v b="$2" 'BEGIN { printf "%.1fs", b - a }'; }

declare -A result timing hint

stage_lint() {
  hint[lint]="run 'uv run ruff check --fix . && uv run ruff format .', then fix what remains by hand."
  run ruff check . && run ruff format --check .
}

stage_types() {
  hint[types]="fix the mypy errors above; do not add 'type: ignore' without a reason in a comment."
  run mypy
}

stage_test() {
  hint[test]="run the failing file alone with 'uv run pytest <path> -x' and fix the first failure."
  run pytest -q
  local code=$?
  if [ "$code" -eq 5 ]; then
    hint[test]="no tests were collected under tests/. Add a test (tdd-behaviour skill) before this stage can pass."
    echo "verify test: pytest collected no tests." >&2
  fi
  return "$code"
}

stage_eval() {
  if ! compgen -G 'evals/dataset*' >/dev/null; then
    result[eval]="skip"
    echo "verify eval: no evaluation set in the tree (evals/dataset*), so this stage is skipped. It becomes a gate once the set is committed."
    return 0
  fi
  hint[eval]="read the evaluation table above. Change a sample's wording, never a recording; only the user changes a threshold."
  run python -m evals.run_eval
}

failed=0
for stage in "${stages[@]}"; do
  echo
  echo "==> $stage"
  start="$(now)"
  if "stage_$stage"; then
    [ "${result[$stage]:-}" = "skip" ] || result[$stage]="pass"
  else
    result[$stage]="FAIL"
    failed=1
  fi
  timing[$stage]="$(elapsed "$start" "$(now)")"
done

echo
echo "verify summary"
printf '  %-6s %-6s %s\n' "stage" "result" "time"
for stage in "${stages[@]}"; do
  printf '  %-6s %-6s %s\n' "$stage" "${result[$stage]}" "${timing[$stage]}"
done

if [ "$failed" -ne 0 ]; then
  echo
  for stage in "${stages[@]}"; do
    if [ "${result[$stage]}" = "FAIL" ]; then
      echo "FAILED $stage: ${hint[$stage]:-see the output above.} Re-run with './scripts/verify.sh $stage'." >&2
    fi
  done
  exit 1
fi
echo
echo "verify: all requested stages passed or were skipped."
