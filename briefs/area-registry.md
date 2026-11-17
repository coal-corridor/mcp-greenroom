# Brief: registry area

Session: its own worktree, branch `area/registry`. Starts when the contracts are frozen. One pull request.

## Goal

The HTTP API, the store, the published list and the audit trail behave as the spec says, working against the fake pipeline until vetting is merged.

## Owns

`src/mcp_greenroom/api/`, `src/mcp_greenroom/store/`, `tests/api/`, `tests/contract/`, `tests/failure/`. Nothing else.

## Read first

`docs/specs/mcp-greenroom.md` (the parent: decision order, invariants, shared criteria), then `docs/specs/registry.md` in full. No other child spec. The pinned OpenAPI document in `contracts/`.

## Deliver

1. The application in the layout of the FastAPI guide for larger applications (`main.py`, `dependencies.py`, one router module per resource), with the pipeline, the provider and the store behind the injection point frozen in the contracts.
2. Submit, status, review and audit read. Identity comes from the caller's credential. Stub identities work only in the dev environment.
3. Separation of duties on the server: the reviewer is never the submitter, and the check compares identities.
4. Resubmission rules: identical content returns the existing decision, other content under a decided name and version is refused.
5. `GET /v0.1/servers` in the upstream format, with cursor paging, holding only approved versions and nothing MCP Greenroom produced.
6. The last-good copy, written atomically on every publish, and served with a degraded marker when the store fails. New submissions are then refused. Readiness says why it is not ready.
7. Liveness and readiness endpoints. One structured log line per request and per decision.
8. Audit records for every decision and every validation refusal. No update or delete path exists.

## Tests to write first

The list response validated against the pinned OpenAPI document. Each refusal with its status code and rule id. Reviewer equals submitter. Store down, broken at the store. An audit record for every decision. No stack trace in any error body.

## Done when

`./scripts/verify.sh quick` and the tests of this area pass in this worktree, and each criterion in `docs/specs/registry.md` names its test, as do the two shared criteria in the parent that this area serves: "Main path" and "Immutable versions".

## Cut first

Nothing here is on the cut list. If time runs short, say so early: the cut is the user's.

## Stop and ask

The upstream format cannot hold something the spec asks for. A criterion needs a change to a frozen model. Degrade mode can only be shown with a flag in the handler.
