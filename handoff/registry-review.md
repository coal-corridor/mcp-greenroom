## Review of area/registry against `mcp-greenroom.md` and `registry.md`

I found no hard failure on the safety points (2, 3, 5, 6, 8). Point 1 fails on one test that proves nothing, and on two "Done" claims that only hold against the fake pipeline. Point 4 fails twice: unknown routes return errors with no rule id, and every unhandled exception is logged raw by uvicorn, outside `log_event`.

### The eight points

**1. Every claimed criterion has a test that asserts it: FAIL.** Rule applied: a test must fail if the claimed behaviour is missing.
- **The refusal test is vacuous.** `tests/api/test_refusal.py:28-35` (`test_a_refusal_stores_no_decision`) resubmits with the version changed from `latest` to `1.0.0`. That is a different name and version, so it returns 201 whether or not the refusal stored anything. Nothing else asserts that a 422 leaves no decision behind. The code looks correct (a refusal only writes an audit event), but no test proves it.
- **Two criteria are overclaimed.** `handoff/registry.md:16-17` marks Main path and Validation rejection as Done. Both are tested only against `FakePipeline`. The rule id asserted is `fake.version_not_pinned`, and `get_pipeline` still raises `NotImplementedError` (`handoff/registry.md:33`). So `make run` returns 500 on every submit. Working against the fake is allowed until vetting merges, but these two criteria should be marked "API side only, not met end to end".
- Smaller gaps:
  - No audit read-back test for a decline. `tests/api/test_audit.py` covers approve only.
  - `tests/api/test_review.py:60` asserts only `!= 200`. It passes on the 422 that `extra="forbid"` produces, so it shows the extra field is rejected, not that identity comes from the credential. The submitter test at :37 does cover that.

**2. No path approves a stopped, failed, missing or uncertain case: PASS.**
- The registry publishes only when the decision it is given says approved (`store/sql.py:235-236`).
- A pipeline crash returns 500 and stores nothing (`tests/failure/test_pipeline_crash.py`).
- A review can only act on `human_review`. A rejected case returns 409 (`store/sql.py:213`, `routers/reviews.py:90`).
- The API trusts `decision.outcome` from the pipeline and has no guard of its own. The spec puts that responsibility in vetting.

**3. Separation of duties is enforced on the server, from the credential: PASS.**
- Identity comes only from the bearer header (`api/dependencies.py:33-55`).
- The check compares identities, not roles (`routers/reviews.py:52`).
- The review body forbids extra fields (`routers/reviews.py:31`).
- Stub tokens only work when `env == "dev"`, which is tested.

**4. Errors carry a rule id and no stack trace; untrusted text is never logged or printed raw: FAIL.**
- **Unhandled exceptions are logged raw.** `api/errors.py:58-65,73` registers a catch-all `Exception` handler. Starlette's `ServerErrorMiddleware` always re-raises after the handler runs (I checked `starlette/middleware/errors.py:183-186`). Uvicorn then logs the full traceback and the exception message, outside `log_event`. A pydantic `ValidationError` raised inside vetting quotes `input_value`, which can be a tool description. Meanwhile the structured line keeps only the exception type. So the operator gets no usable detail through the sanctioned logger, and raw untrusted text through the unsanctioned one. The tests use `raise_server_exceptions=False`, which hides this.
- **Unknown routes return no rule id.** `api/errors.py:70` registers the handler for `fastapi.HTTPException`. Unknown-route 404s and 405s are raised as Starlette `HTTPException`, and lookup follows the exception's own class hierarchy (`starlette/_exception_handler.py:17`). So FastAPI's default handler answers with `{"detail":"Not Found"}`. There is no stack trace, but no rule id either.
- Possible issue (low, not sure it breaks the rule): `routers/submissions.py:55` and `api/errors.py:39` put pydantic field paths into the message. With `extra="forbid"` those paths include key names the attacker chose. They are JSON-escaped, so they are not printed raw in the HTTP body. I cannot tell from this diff how a client prints them.

**5. No network calls in tests or the check script; no secrets in the diff: PASS.**
- The only tokens are the stub `dev-*` tokens.
- One caveat: `tests/api/test_operability.py:70-78` starts a subprocess with the full `os.environ`. That subprocess is outside the socket guard in `tests/conftest.py`. It makes no network call today because config fails first.
- Related: `api/main.py:73` builds the app at import time. Every test that imports `create_app` therefore reads the developer's `.env`, and a bad local `.env` makes the whole suite exit at collection.

**6. Every decision writes an audit record with the policy version; no update or delete: PASS.**
- The policy decision and its audit events are written in one transaction (`store/sql.py:191-204`). The human decision is written the same way (`store/sql.py:209-216`). A refusal also writes an event.
- Triggers block UPDATE and DELETE on `audit_events`, `decisions` and `published` (`store/tables.py:56-64`), and this is tested.
- Possible issue: a refusal records `settings.policy_version` (`routers/submissions.py:80`), while decisions record the pipeline's version. They already differ in the tests (`fake-policy` against `2026-11-17.1`). Whether they agree once vetting is wired depends on vetting.

**7. Nothing outside the spec's scope: PASS.**
- Cursor paging is required by the spec.
- Putting the degraded marker in headers is a choice the spec did not ask for. It is documented, and it keeps the body in upstream format. A client that reads only the body cannot tell the list is degraded.

**8. No test weakened: PASS.** All test files are new. The only removals in `dependencies.py` are the `NotImplementedError` stubs. There are no skip or xfail markers.

### The other items you asked for

**Modules doing more than one job**
- `routers/submissions.py:29-48,93-100,173-183` is a router, and also holds the shared response model and helpers that `reviews.py` imports.
- `store/sql.py:133-151,242-247` handles persistence, and also builds the upstream format (the `_meta` official block) and runs snapshot writes.

**Loosely typed boundaries**
- `api/dependencies.py:26-29`: `get_store` returns the empty `Store` Protocol from `app.state` (typed `Any`). The routers annotate the parameter as `SqlStore` (`routers/audit.py:25`, `routers/servers.py:26`, and others), so mypy never checks that the two match.
- `store/snapshot.py:35` and `api/paging.py:33-34`: the snapshot is unvalidated `list[dict[str, Any]]`, served as the approved list in degrade mode. A wrong-shaped record raises `KeyError`, which becomes a 500 instead of a 503.

**Errors swallowed or surfaced without a usable message**
- `store/sql.py:242-247`: a failed snapshot write is logged with the exception type only, and `/readyz` does not report it. The degraded list can then go silently stale.
- `api/main.py:45-49`: a store failure at startup is swallowed by design (degrade). But `ensure_schema` never runs again, so the app stays unusable until restart even after the database recovers. Also, a fresh empty database at startup overwrites the last-good copy with an empty list (`api/main.py:47`). I am not sure the second part matters in practice.
- `store/sql.py:216` and `routers/reviews.py:90-95`: every `IntegrityError` during a review becomes `NotPending`. In a race, the 409 message would read "this submission is human_review, not in human review".

### Findings, most severe first

| Finding | Severity | File and line | Suggested fix |
|---|---|---|---|
| Unhandled exceptions are re-raised by Starlette and logged raw by uvicorn (untrusted text, outside `log_event`); the structured line has only the exception type | High | `src/mcp_greenroom/api/errors.py:58-65,73` | Turn unexpected errors into the 500 response in a middleware so nothing re-raises, and log through `log_event` with type plus a hashed or redacted message; add a test that runs with `raise_server_exceptions=True` |
| `test_a_refusal_stores_no_decision` passes whatever the code does | High | `tests/api/test_refusal.py:28-35` | Assert `GET /submissions/{refusal id}` returns 404, or refuse a pinned version for another reason (no tools), then resubmit the same name and version and expect 201, not 409 |
| Main path and Validation rejection marked Done but proven only against the fake; real submit returns 500 | Medium | `handoff/registry.md:16-17,33` | Mark them "API side only, not met end to end" until integration wires `get_pipeline` |
| Unknown-route 404/405 bodies have no `rule_id` | Medium | `src/mcp_greenroom/api/errors.py:70` | Register the handler on `starlette.exceptions.HTTPException` |
| Snapshot write failure is silent and invisible to `/readyz`; the degraded list can go stale | Medium | `src/mcp_greenroom/store/sql.py:242-247` | Report snapshot age or failure in `/readyz`, and list the gap in `operate.md` |
| Snapshot served without validation; a malformed record gives 500 | Low | `src/mcp_greenroom/store/snapshot.py:35`, `src/mcp_greenroom/api/paging.py:33-34` | Validate the record shape on read and treat a bad record as `SnapshotMissing` |
| Startup schema failure is never retried; an empty database at startup wipes the last-good copy | Low (not sure) | `src/mcp_greenroom/api/main.py:45-49` | Retry `ensure_schema` lazily; skip the snapshot refresh at startup |
| `get_store` returns the empty `Store` Protocol while routes annotate `SqlStore` | Low | `src/mcp_greenroom/api/dependencies.py:26-29` | Return `SqlStore`, or ask the lead to fill in the `Store` Protocol |
| App built at import time reads the local `.env` in tests; subprocess test inherits the full environment | Low | `src/mcp_greenroom/api/main.py:73`, `tests/api/test_operability.py:70-78` | Build the app lazily (a factory for `make run`); pass a minimal env to the subprocess |
| Refusal audit uses the settings policy version, decisions use the pipeline's | Low (not sure) | `src/mcp_greenroom/api/routers/submissions.py:80` | Confirm at integration that both come from the same source |
| Any `IntegrityError` in a review becomes "not pending", with a misleading message | Low | `src/mcp_greenroom/store/sql.py:216`, `src/mcp_greenroom/api/routers/reviews.py:90-95` | Catch only the `uq_decision_seq` violation; reword the race message |
| No audit read-back test for a decline; body-identity test only asserts `!= 200` | Low | `tests/api/test_audit.py`, `tests/api/test_review.py:60` | Add a decline read-back; assert 422 `request.invalid` and that the case is unchanged |
| Router module also holds shared helpers; store also builds the upstream format | Low | `src/mcp_greenroom/api/routers/submissions.py:29-48,93-100,173-183`, `src/mcp_greenroom/store/sql.py:133-151` | Move the helpers to `api/results.py` and the format code to its own module |

### Decisions (the user's, one per finding above, in the same order)

1. Unhandled exceptions logged raw by uvicorn.
   **Decision:** fix now.
2. `test_a_refusal_stores_no_decision` is vacuous.
   **Decision:** fix now.
3. Main path and Validation rejection overclaimed.
   **Decision:** fix now; mark them "API side only, not met end to end" in the handoff note.
4. Unknown-route 404/405 without a `rule_id`.
   **Decision:** fix now.
5. Silent snapshot write failure, invisible to `/readyz`.
   **Decision:** fix now, last, and only if the others are green by 15:30. Otherwise defer and say so.
6. Snapshot served without validation.
   **Decision:** defer to the roadmap.
7. Startup schema failure never retried; empty database wipes the last-good copy.
   **Decision:** defer; note it for `operate.md`.
8. `get_store` typing against the empty `Store` Protocol.
   **Decision:** defer to integration; the lead fills the `Store` protocol.
9. App built at import time; subprocess test inherits the full environment.
   **Decision:** fix the subprocess now by passing a minimal environment. Defer the import-time build.
10. Two policy version sources.
    **Decision:** defer to integration; the lead confirms one source.
11. Any `IntegrityError` in a review becomes "not pending".
    **Decision:** defer to the roadmap.
12. No decline read-back test; body-identity test asserts only `!= 200`.
    **Decision:** fix now.
13. Module responsibilities.
    **Decision:** accept; no refactor in this slice.

Fix order: 1, 2, 4, 12, 9, 3, 5.
