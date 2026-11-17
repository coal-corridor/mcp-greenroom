# Roadmap: MCP Greenroom

Status on 17 Nov 2026: Phase 1 is built. Everything after that is future roadmap.

## Phase 1: the slice

- **Done:** submission and review API (submit, status, review, audit read)
- **Done:** vetting pipeline (validation, own rules, fingerprint, fixed decision order)
- **Done:** LLM risk classifier (replays recorded answers by default, live provider as an option)
- **Done:** scanner rules (Cisco MCP Scanner, YARA engine, offline)
- **Done:** registry endpoint `GET /v0.1/servers`, with a last-good copy when the store is down
- **Done:** append-only audit trail
- **Done:** `mcp-greenroom` CLI, client simulator, demo script, check script, container files
- **Done:** evaluation set of 41 cases with a hard gate: no malicious sample is approved by policy
- **Done:** the five safe failures, shown by the demo script
- **Done:** README and evidence pack
- **Partly:** pull request checks. All five jobs run and are green. They are not yet marked required, because the repo was private during the build
- **Not built:** the five stretch items (tracing, submission by upstream reference, interactive menu, per-version endpoints, shadowing rule)

## Deferred from the area reviews

Status: not started. The finding and the decision are in the review file named.

- Validate snapshot records on read (registry review 6)
- Retry the schema setup after a failed start, and keep an empty database from wiping the last-good copy (registry review 7)
- Build the app lazily, so tests never read a local `.env` (registry review 9)
- Report only the real "not pending" case on a review conflict (registry review 11)
- Stamp each decision with a hash of the thresholds and the require-human flag (vetting review 4)
- Refuse duplicate tool names (vetting review 11)
- Build the install command ourselves instead of refusing a list of arguments (vetting review 3)
- Allowed package sources as a setting (vetting handoff)
- Version-aware matching in the client simulator (edge review 3)
- Parse `docker run` in client configs (edge review 4)
- Keep the degraded flag in `list --json` (edge review 6)
- CLI errors that name the field (edge review 8)
- `list` fails visibly at the page cap (edge review 9)
- Keep serving the last-good list when the pipeline cannot be built (integration review 3)
- Stricter `read_submission`: a JSON object check and tests for read errors (integration review 6)

## Phase 2: pilot in one organisation

Status: not started.

1. Single sign-on, with roles from directory groups
2. Managed PostgreSQL with schema migrations
3. Live classifier on an in-region model endpoint
4. Human approval for every server as the default policy
5. Package digest in the submission, and sources narrowed to the internal artifact repository
6. Withdraw or deprecate an approved version
7. Per-version endpoints, search and CORS on the read path
8. Export of the approved set as a managed-settings allowlist
9. Tests against live Amp and Copilot workspaces
10. Reviewer screen, notifications and a lead-time metric
11. Deployment through environments, image scan, a required second reviewer, a blocking dependency audit
12. Audit events streamed to the SIEM and to immutable storage
13. Maximum age and an alert for the degraded list
14. Metrics, dashboards and traces to the organisation's collector
15. Dry run for developers

## Phase 3: assurance at scale

Status: not started.

1. Sandbox introspection of the submitted server's real tool list
2. Scheduled drift checks, and re-vetting on a policy, prompt or model change
3. Upstream references with a live fetch from trusted registries
4. More scanner engines as evidence sources
5. Policy as code, per business unit
6. Larger evaluation set, fed by real review outcomes
7. Loader or gateway integration for agent libraries with no central setting
8. Evidence export for audits

## Out of scope

Status: not planned.

- Inspecting or blocking tool calls at runtime (belongs to an MCP gateway)
- Detecting a server modified on a laptop after approval (device management)
- Hosting or mirroring server packages (the artifact repository)
- Live links to other registries
- Approval by the model alone
- Marketplace features: ratings, popularity, browsing
- Source code audit of submitted servers (the owning team's pipeline)
- Per-user authorisation of individual tool calls (the gateway)
- Data loss prevention on tool traffic (the gateway)
- Skills, plugins and other agent extensions that are not MCP servers