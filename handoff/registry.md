# Handoff: registry on area/registry

State at commit d035b6c (2026-11-17). Uncommitted files: none.

## Goal
HTTP API, store, published list and audit trail as `docs/specs/registry.md` says, against the fake pipeline until vetting merges.

## Plan
1. Setup: `uv sync`, `./scripts/verify.sh quick`, save the plan with `handoff`.
2. Store (`store/`): SQLAlchemy sync on SQLite, append-only audit, StoreUnavailable on DB errors, atomic last-good snapshot on publish.
3. API (`main.py`, `dependencies.py`, one router per resource): bearer identity, submit/status/review/audit, 422/409/403 rules.
4. `GET /v0.1/servers` upstream format with cursor; degrade mode; liveness, readiness, one log line per request and decision.
5. Red/green per behaviour, then `verify-change`, criteria mapped to tests here.

## Done (each criterion and its test)
- Main path (parent): API side only, not met end to end (fake pipeline). tests/api/test_submit.py, tests/contract/test_server_list.py
- Validation rejection (parent): API side only, not met end to end (fake rule id). tests/api/test_refusal.py
- Immutable versions (parent): tests/api/test_resubmission.py, test_refusal.py::test_a_refusal_stores_no_decision
- Standard format: tests/contract/test_server_list.py. Separation of duties: tests/api/test_review.py
- Degrade mode: tests/failure/test_degrade.py, tests/failure/test_snapshot_failure.py
- Audit: tests/api/test_audit.py. Operability: tests/api/test_operability.py, test_degrade.py
- Review fixes 1, 2, 4, 12, 9, 5 done (handoff/registry-review.md): commits 809b877, 755ecf2, d9ba664, 37150b4, 4f7ea53, d035b6c

## Checks
  lint   pass   0.1s
  types  pass   0.2s
  test   pass   5.4s   (99 passed)
  eval   skip   0.0s

## Open
1. Integration: wire `get_pipeline` (real submit returns 500 until then); lead fills `interfaces.Store` (review 8) and confirms one policy-version source (review 10).
2. Deferred, see the review: 6 and 11 to the roadmap; 7 for operate.md; 9 import-time app build; 13 accepted.
3. Open the area PR when the user says so.

## Decisions and corrections
- `get_identity` taking the header is not a contract change. Work the brief without check-ins; commit each green route.
- Degraded marker in headers (`X-Greenroom-Degraded`, `X-Greenroom-Generated-At`); body stays upstream. No expiry.
- Store methods on `store.SqlStore`; paging in Python over the full list, same code for DB and snapshot.
- User's decisions on the review, per finding, are in handoff/registry-review.md.

## Question at the impasse
none

## Next step
User runs /open-area-pr.
