# Handoff: edge on area/edge

State at commit e54a9b8 (2026-11-17). Uncommitted files: none (this note aside).

## Goal
Drive every step of the demo from the `mcp-greenroom` CLI over HTTP, plus a client simulator of Amp's documented registry check (briefs/area-edge.md).

## Plan
As approved: setup; client simulator; CLI skeleton with client-check; exit codes and status words; inert printing; then the other commands from area/registry's routes (user: read them from that branch, do not ask).

## Done
- Client check: tests/e2e/test_client_sim.py (listed, unlisted, unreachable, unusable reply, paging, runner arguments).
- CLI, seven commands: tests/e2e/test_cli.py, test_cli_submit.py, test_cli_commands.py (exit codes, --json, no colour, inert text, help, --debug).
- End to end: tests/e2e/test_e2e.py skips only while api/main.py is absent; on a scratch merge with area/registry 6c0b5f1: 68 e2e passed, demo --fake all 15 steps as expected.
- Review (handoff/edge-review.md): fixed 4 runner parsing, 1 e2e skip, 7 inert values, 11 no local .env in tests, 5 --json only when JSON.
- Dockerfile, docker-compose.yml, .dockerignore, deploy/README.md: image built and ran healthy on a scratch merge.

## Checks
  lint   pass   0.1s
  types  pass   0.2s
  test   pass   1.0s   (110 passed, 1 skipped: e2e, no API on this branch)
  eval   skip   0.0s

## Open
1. Integration: drop `--fake` once vetting wires get_pipeline; save demo output in evidence/verify.md.
2. The image copies evals/recordings: builds once vetting commits it. Spinner not built (cut first).
3. cli.py is at 348 of 350 lines: the next change there needs room first.
4. Roadmap (user): version-aware client matching; parse `docker run` (docker servers are blocked today); `list --json` degraded flag; errors naming the field, not the exception class; `list` failing at the page cap.

## Decisions and corrections
- User: continue without check-ins; edge owns cli_output.py; .dockerignore approved this session (one file outside edge's folders).
- User on review: version-blind matching follows the spec; `--json` passes hidden characters through as machine output; cli_output.py stays as is.
- client-check exits 20 when any server is blocked, unreachable registry included; `review` exits 0 when recorded.
- Slips: red commit 4dace08 typed `fix(edge)`; 3c735e5 had a lint failure hidden by a pipe, fixed in f6e0bd5.

## Question at the impasse
none

## Next step
Pull request area/edge -> main opened with `/open-area-pr`: watch its checks; the user merges.
