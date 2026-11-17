# Contracts: pinned upstream documents

Fetched on 2026-11-17 and not edited since. Frozen: a change here is a question to the user, never a local fix. Re-fetch only on purpose, update this table in the same commit, and say what changed.

| File | Source | Version | sha256 |
| --- | --- | --- | --- |
| `registry-openapi.yaml` | https://raw.githubusercontent.com/modelcontextprotocol/registry/115f85225c9fac5281d8a2dc8551cf49b004d2f9/docs/reference/api/openapi.yaml | `info.version` 2025-12-01, OpenAPI 3.1.0 | `4e3d5e7848ebb28bd7206cff5d4523bb3046bd62c77491d4945c2aa831e4f0a8` |
| `server.schema.json` | https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json | `$id` 2025-12-11, JSON Schema draft-07 | `3fba09590c99f61735d234822279f4223fab9e300c0a81e81c91ab62a4114de0` |

The OpenAPI document is taken from `modelcontextprotocol/registry` at commit `115f852` (the head of `main` on 2026-11-17). The schema is the versioned URL itself.

## Licence

`modelcontextprotocol/registry` is moving from MIT to Apache-2.0. Its `LICENSE` file says new code and specification contributions are Apache-2.0, other documentation is CC-BY-4.0, and older contributions with no relicensing consent stay MIT. Neither file states which of these applies to it. Both are vendored unchanged, for validation only, and the upstream notice is kept by linking it here: https://github.com/modelcontextprotocol/registry/blob/115f85225c9fac5281d8a2dc8551cf49b004d2f9/LICENSE

## Checked against the spec on 2026-11-17

- Versions match the ones seen on 16 Nov 2026: 2025-12-01 and 2025-12-11.
- The list endpoint is `GET /v0.1/servers`. It returns one record per server version and pages with `metadata.nextCursor` and the `cursor` query parameter.
- `name` is reverse-DNS with exactly one slash, for example `com.examplebank/payments-readonly`.
- `server.json` carries no tool definitions. MCP Greenroom takes tools as a separate part of a submission. Only the `server.json` part is ever published.
