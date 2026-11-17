# Handoff: registry on area/registry

State at commit 6670fea (2026-11-17). Uncommitted files: none.

## Goal
HTTP API, store, published list and audit trail as `docs/specs/registry.md` says, against the fake pipeline until vetting merges.

## Plan
1. Setup: `uv sync`, `./scripts/verify.sh quick`, save the plan with `handoff`.
2. Store (`store/`): SQLAlchemy sync on SQLite, append-only audit, StoreUnavailable on DB errors, atomic last-good snapshot on publish.
3. API (`main.py`, `dependencies.py`, one router per resource): bearer identity, submit/status/review/audit, 422/409/403 rules.
4. `GET /v0.1/servers` upstream format with cursor; degrade mode; liveness, readiness, one log line per request and decision.
5. Red/green per behaviour, then `verify-change`, criteria mapped to tests here.

## Done (each criterion and its test)
- Main path (parent): tests/api/test_submit.py, tests/contract/test_server_list.py::test_list_holds_only_approved_versions_in_upstream_format
- Validation rejection (parent): tests/api/test_refusal.py
- Immutable versions (parent): tests/api/test_resubmission.py, test_refusal.py::test_a_refusal_stores_no_decision
- Standard format: tests/contract/test_server_list.py (incl. cursor paging)
- Separation of duties: tests/api/test_review.py
- Degrade mode: tests/failure/test_degrade.py (SQLite file overwritten, no handler flag)
- Audit: tests/api/test_audit.py (incl. triggers refusing UPDATE/DELETE)
- Operability: tests/failure/test_degrade.py (livez/readyz), tests/api/test_operability.py
- Stub identities dev only: tests/api/test_identity.py. Fail closed on crash: tests/failure/test_pipeline_crash.py

## Checks
  lint   pass   0.1s
  types  pass   0.2s
  test   pass   4.6s   (93 passed)
  eval   skip   0.0s

## Open
1. `get_pipeline` still raises NotImplementedError: real submit returns 500 until vetting merges (integration wires it).
2. Open the area PR once the user says so.

## Decisions and corrections
- User: `get_identity` taking the header is not a contract change. Work through the brief without check-ins; commit each green route.
- Degraded marker is in headers (`X-Greenroom-Degraded`, `X-Greenroom-Generated-At`) so the body stays upstream format. No expiry (spec's first move).
- Store methods live on `store.SqlStore`; `interfaces.Store` left empty (outside my folders).
- Paging is done in Python over the full published list, same code for DB and snapshot.

## Question at the impasse
none

## Next step
Ask the user whether to open the pull request (`open-area-pr` skill).
