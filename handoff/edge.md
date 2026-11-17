# Handoff: edge on area/edge

State at commit 60e0a8b (2026-11-17). Uncommitted files: none (this note aside).

## Goal
Drive every step of the demo from the `mcp-greenroom` CLI over HTTP, plus a client simulator of Amp's documented registry check (briefs/area-edge.md).

## Plan
As approved: setup; client simulator; CLI skeleton with client-check; exit codes and status words; inert printing; then the other commands from area/registry's routes (user: read them from that branch, do not ask).

## Done
- Client check: tests/e2e/test_client_sim.py (listed allowed, unlisted blocked, unreachable and unusable reply block all, paging).
- CLI, all seven commands: tests/e2e/test_cli.py, test_cli_submit.py, test_cli_commands.py. Exit codes per outcome and per error, `--json` equals the API body, no colour when piped or NO_COLOR, inert findings/names/errors, --help with one example, no trace without --debug.
- End to end: tests/e2e/test_e2e.py, skipped on this branch (no API); 149 passed on a scratch merge with area/registry at 600b2f8.
- scripts/demo.sh (`--fake` uses tests/e2e/fake_service.py): main path and the five safe failures, all 15 steps at the expected exit code on the scratch merge.
- Dockerfile, docker-compose.yml, deploy/README.md: image built and ran on the scratch merge; `health` showed live, ready, normal.

## Checks
  lint   pass   0.1s
  types  pass   0.2s
  test   pass   0.9s   (98 passed, 1 skipped)
  eval   skip   0.0s

## Open
1. At integration: drop `--fake` once vetting wires get_pipeline; save demo output in evidence/verify.md.
2. The image copies evals/recordings: builds only once vetting commits it.
3. No .dockerignore (outside edge's folders): build context includes .venv. Spinner not built (cut first).

## Decisions and corrections
- User: continue without check-ins; read registry routes from area/registry.
- User: edge also owns src/mcp_greenroom/cli_output.py (350-line limit); recorded in the brief.
- client-check exits 20 whenever a server is blocked, including registry unreachable (spec's client-check rule).
- `list --json` is one ServerList of every page; `review` exits 0 when recorded; error body read flat, as registry sends it.
- Slip: red commit 4dace08 typed `fix(edge)`, not `test(edge)`. 3c735e5 went in with a lint failure hidden by a pipe, fixed in f6e0bd5.

## Question at the impasse
none

## Next step
Ask the user whether to open the edge pull request (`open-area-pr` skill).
