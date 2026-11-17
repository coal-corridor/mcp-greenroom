# Handoff: lead on setup

State at commit 0b4ecd9 (2026-11-17). Uncommitted files: none.

## Goal
Brief 00: before any feature exists, the repo has one check script, PR checks that call it, and guard rails. Lands in the setup PR with brief 10.

## Plan
Approved 2026-11-17. One commit each:
0. Branch `setup` from `main` (done). No baseline commit: `main` already has 3 pushed commits.
1. `pyproject.toml` (the parent spec's stack, dev group, ruff `S` set), `.python-version` 3.12, empty `src/mcp_greenroom/`, `uv.lock`.
2. `scripts/verify.sh`: lint/types/test/eval/quick/all, runs every stage, summary table with result and time, eval skipped until a dataset exists. Commit while `test` fails.
3. `tests/conftest.py`: guard that blocks outbound connections except to localhost.
4. `tests/structure/`: 350-line limit; only the config module reads env vars.
5. `.github/workflows/ci.yml`: `verify (quick|test|eval)`, `secret scan` (gitleaks, full history), non-blocking `uv audit`. Read-only permissions, actions pinned to SHAs, uv pinned.
6. `Makefile`: verify, run, demo, record.

## Done
Nothing built yet. Branch `setup` created from `main` at 0b4ecd9.

## Checks
`./scripts/verify.sh` does not exist yet (plan item 2).

## Open
Plan items 1 to 6 in order, then brief 10 (contracts) in the same PR.

## Decisions and corrections
- The repo is private for now, so required checks can't be switched on yet. The user merges on green by hand. Not a blocker.
- No baseline commit: `main` already had 3 pushed commits (verified with `git log`).
- If `cisco-ai-mcp-scanner` does not resolve or install cleanly, leave it out of `pyproject.toml` and tell the user. Don't debug it in this phase.
- "Full script fails only on test" applies at commit 2. After items 3 and 4, `test` should pass.

## Question at the impasse
none

## Next step
Plan item 1: write `pyproject.toml` and run `uv lock`.
