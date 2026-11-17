# Handoff: edge on area/edge

State at commit 2ca2349 (2026-11-17). Uncommitted files: none.

## Goal
Drive every step of the demo from the `mcp-greenroom` CLI over HTTP, plus a client simulator of Amp's documented registry check (briefs/area-edge.md).

## Plan
1. Setup: `uv sync`, `./scripts/verify.sh quick`, this note.
2. Client simulator `src/mcp_greenroom/client_sim.py`, labelled a simulation: reads a config in `sample-data/client-configs/` (Amp `amp.mcpServers` shape; npx -> npm, uvx -> pypi, docker -> oci), pages `GET /v0.1/servers` (pinned OpenAPI) through an injected httpx client, matches (registryType, identifier). Tests: listed allowed, unlisted blocked, unreachable or malformed blocks all.
3. CLI skeleton `src/mcp_greenroom/cli.py`: bare command prints name, tagline, commands; `--api`/`--token` from `load_settings`; `client-check CONFIG` exits 0 / 20 / 1. CliRunner + httpx.MockTransport.
4. Exit codes and status words as pure functions: approved 0, review 10, rejected 20; 401/5xx/unreachable 1; 403/409/422 20. `✓ approved`, `! needs review`, `✗ rejected`; no colour when piped or NO_COLOR.
5. Inert printing helper (escape markup, show Cc/Cf/separators as \uXXXX), red test with markup, ANSI and zero-width text. Then ask the user for route shapes before submit/status/review/audit/list/health.
Tests live in `tests/e2e/` (the only test folder the brief grants).

## Done
- `uv sync` done; `./scripts/verify.sh quick` passes (lint, types).

## Checks
  stage  result time
  lint   pass   0.1s
  types  pass   0.1s
  test   pass   1.2s
  eval   skip   0.0s

## Open
Plan items 2 to 5, in order. Then route shapes, demo.sh, e2e test, container files.

## Decisions and corrections
- The user approved the five-line plan. No Greenroom route shape is assumed without asking.

## Question at the impasse
none

## Next step
Red test: listed server is allowed, in `tests/e2e/test_client_sim.py`.
