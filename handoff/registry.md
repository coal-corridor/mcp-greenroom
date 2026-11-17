# Handoff: registry on area/registry

State at commit 2ca2349 (2026-11-17). Uncommitted files: none.

## Goal
HTTP API, store, published list and audit trail as `docs/specs/registry.md` says, against the fake pipeline until vetting merges.

## Plan
1. Setup: `uv sync`, `./scripts/verify.sh quick`, save the plan with `handoff`.
2. Store (`store/`): SQLAlchemy sync on SQLite: submissions, decisions, append-only audit events (insert and read only). Store raises its own error on a database failure. Last-good snapshot written atomically on every publish.
3. API (`api/main.py`, `dependencies.py`, one router per resource): bearer identity from `config.DEV_IDENTITIES` (401 otherwise); submit, status, review, audit read; 422 + rule id + audit event on `Refusal`; identical resubmit returns the stored decision, other content gets 409; 403 on self-review or non-reviewer; note required.
4. `GET /v0.1/servers`: upstream format, cursor paging, approved only. Store down: serve snapshot marked degraded, submissions 503, readiness says why. Liveness, readiness, one log line per request and per decision, no stack trace in error bodies.
5. Red/green per behaviour, in order: main path, list vs pinned OpenAPI, 422 refusal, immutable versions, separation of duties, audit read-back, degrade mode, operability. Then `verify-change` and map each criterion to its test here.

## Done
- Setup: `uv sync` ok, `./scripts/verify.sh quick` green.

## Checks
  lint   pass   0.1s
  types  pass   0.2s
  test   pass   1.3s   (43 passed)
  eval   skip   0.0s

## Open
All of plan items 2 to 5.

## Decisions and corrections
- Plan approved by the user as written above.

## Question at the impasse
none

## Next step
Red test for the main path: `tests/api/test_submit.py` (payments-readonly 1.2.0 as dev-dana, approved, tier low, reasons, under 5 s).
