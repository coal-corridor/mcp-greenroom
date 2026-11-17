# Spec, child: registry

Read the parent first: `docs/specs/mcp-greenroom.md`. Its decision order,
invariants and scope apply here unchanged. This file adds what only the registry
area must deliver.

### Acceptance criteria

- [ ] **Standard format.** The `GET /v0.1/servers` response validates against
the official MCP registry OpenAPI document vendored in the repo.
- [ ] **Separation of duties.** `ambiguous-exporter` 2.0.0 (sends reports to a
configurable URL: low score, tier medium) is submitted by a reviewer and lands
in human review. That reviewer's approval is refused with 403 and changes
nothing. So is an approval by an identity without the reviewer role. The other
reviewer's approval, with a non-empty note, publishes it.
- [ ] **Degrade mode.** With the database unreachable (broken at the store, not
by a flag in the handler), `GET /v0.1/servers` returns the last published list,
marked as degraded. New submissions are refused with 503. The readiness check
reports not ready and says why.
- [ ] **Audit.** Every policy decision and every human decision can be read
back per submission: actor, action, time, reasons, policy version. A validation
refusal leaves an audit event too. The store has no update or delete for audit
records.
- [ ] **Operability.** Liveness and readiness endpoints exist. Each request and
each decision writes one structured log line. Invalid configuration stops
startup with a clear message.

### Build constraints

- Upstream documents: fetch the MCP registry OpenAPI document and the
`server.json` schema at the start, and pin both in the repo with URL and date.
The versions seen on 16 Nov 2026 were 2025-12-01 and 2025-12-11. The list
returns one record per server version and pages with a cursor. Server names
contain a slash. `server.json` carries no tool definitions.

### Open questions

- How stale may the degraded list get? First move: serve it with its generation
time and no expiry, and list the gap in `operate.md`.
