# Roadmap: MCP Greenroom

Status: specified, not yet built.

Phase 1 is the only committed scope, and the spec is its source of truth. Everything under "Future work" is direction, ordered by priority, with no dates. Platform behaviour mentioned here was read from public documentation on 16 Nov 2026.

## Current status

States: **Done**, **Drafted** (written, open to change), **Specified** (acceptance criteria exist, no code), **Not started**.

| Item | State | Notes |
| --- | --- | --- |
| Problem framing and solution choice | Done | |
| Intent | Drafted | Problem, users, assumptions, success criteria |
| Spec | Drafted | Acceptance criteria, decision order, invariants, cut order |
| README | Drafted | Overview only. Setup, run and example sections follow the build |
| Build environment | Done | Toolchain checked, agent harness trimmed |
| Phase 1 implementation and tests | Specified | |
| Evaluation set and classifier recordings | Specified | Recordings come from one live model run during the build |
| Evidence pack | Drafted (2 of 6) | `intent.md` is drafted and `agentic-workflow.md` is a skeleton. The other four files are written from real output |
| Phase 2 and later | Not started | Direction only |

## Phase 1: the slice (proof of concept)

**Goal.** One workflow, end to end, from a clean checkout with no keys and no network: submit, vet, decide, review, publish, enforce. Built in a three-hour timebox with Claude Code as the primary implementation tool.

### In scope

| Area | What is built |
| --- | --- |
| Submission and review API | Submit, status, review and audit read over HTTP. Three stub identities that work only in the dev environment |
| Vetting pipeline | Schema validation, rule checks (pinned version, allowed package source, hidden characters), a fingerprint of the manifest and tool definitions, one fixed decision order |
| Risk classifier | Scores each tool description for injection risk and tags its capabilities. Sits behind a provider interface: replay of recorded responses by default, a live model on a configurable endpoint as an option |
| Scanner rules | The YARA engine of the open source Cisco MCP Scanner runs offline on every submission. Its findings are evidence. They can stop an approval and never grant one |
| Registry endpoint | `GET /v0.1/servers` in the official MCP registry format, validated against the vendored OpenAPI document. Serves the last good copy when the store is down |
| Audit trail | Append-only record of every decision: actor, action, time, reasons, policy version |
| Tooling | The `mcp-greenroom` CLI (readable output, `--json`, outcome exit codes), a client simulator of the documented Amp check, demo script, one check script (`./scripts/verify.sh`), container files |
| Pull request checks | GitHub Actions on every pull request and every push to `main`, as parallel jobs: lint and types, tests, evaluation (all three through the check script), a secret scan, and a dependency audit that reports without blocking. One pull request per area, merge commits only |
| Evaluation | About 40 labelled synthetic tool descriptions, run inside the check script. Hard gate: no malicious sample is approved by policy |
| Documentation | README and the evidence pack: `intent`, `design`, `agentic-workflow`, `verify`, `operate`, `decisions` |

### Safe failures demonstrated

1. **Validation rejection.** A malformed submission is refused with a stable rule id.
2. **Guarded failure.** A poisoned tool description is rejected, naming the rule, the tool and the offending text.
3. **Abstain.** A case the classifier cannot judge, or cannot answer, goes to human review.
4. **Separation of duties.** A reviewer cannot approve their own submission.
5. **Degrade mode.** With the store down, the registry serves the last published list and reports that it is degraded.

### Stretch

Built only when everything above is green. Listed in the order they are cut, first to last.

1. Tracing: OpenTelemetry spans per vetting stage, viewable in an optional local Jaeger container.
2. Submission by upstream reference: copy a server record from the official MCP registry or another subregistry instead of supplying the manifest.
3. An interactive menu over the CLI commands, with a listing of the cases waiting for review.
4. Per-version lookup endpoints on the read path.
5. A rule for tool names that shadow an already approved server.

### Exit criteria

- `./scripts/verify.sh` is green in a fresh clone, with no network and no credentials.
- The required pull request checks are green on the last commit of `main`, and the dependency audit result is stated in `evidence/verify.md`.
- The demo script shows the main path and the five safe failures, and its real output is saved in `evidence/verify.md`.
- Every acceptance criterion in the spec is met and names the test that proves it.
- The README and all six evidence files exist, written from real output, with known gaps stated.
- Commit history is incremental and never rewritten.

### Limits accepted in Phase 1

| Limit | Addressed by |
| --- | --- |
| Vets the tools a submitter declares, not what the running server exposes | Phase 3, item 1 |
| An approval is not bound to the package bytes | Phase 2, item 5 |
| Stub identities, SQLite, single node | Phase 2, items 1, 2 and 11 |
| By default the classifier only knows recorded samples | Phase 2, item 3 |
| An approved version cannot be withdrawn | Phase 2, item 6 |
| Platform behaviour is simulated from documentation | Phase 2, item 9 |
| Approval is per version, but Amp's check matches package name and registry type only | Not fixable inside MCP Greenroom. Confirmed or corrected by Phase 2, item 9 |
| The degraded list has no expiry | Phase 2, item 13 |
| The dependency audit reports and does not block a merge | Phase 2, item 11 |

### Deferred from the area reviews

One line each. The finding and the user's decision are in the review file named.

- Validate snapshot records on read; a malformed record gives 500 today (registry review 6).
- Retry `ensure_schema` after a failed start, and stop an empty database at startup from wiping the last-good copy (registry review 7, also in `operate.md`).
- Build the app lazily instead of at import time, so tests never read a local `.env` (registry review 9).
- Report only the `uq_decision_seq` violation as "not pending"; any other `IntegrityError` reads the same today (registry review 11).
- Stamp each decision with the policy version plus a hash of the thresholds and require-human flag, so any policy change gives a new version; today startup only refuses a change away from the defaults under the default version (vetting review 4).
- Refuse duplicate tool names at step 1 (`validation.duplicate_tool`); today the evidence can name the wrong tool (vetting review 11).
- Build the install command ourselves instead of refusing a list of registry-override arguments, which cannot be complete (vetting review 3).
- Allowed package sources as a setting; today a strict list in `vetting/policy.py` tied to policy 2026-11-17.1 (vetting handoff).
- Version-aware client matching in the client simulator (edge review 3).
- Parse `docker run` in client configs; Docker servers are blocked today (edge review 4).
- Keep the degraded flag in `list --json` (edge review 6).
- CLI errors that name the field, not the exception class (edge review 8).
- `list` that fails visibly at the 1000-page cap instead of stopping silently (edge review 9).
- Keep serving the last-good list when the pipeline cannot be built at startup; today startup stops with a clear message and nothing is served (integration review 3).
- `read_submission` checks for a JSON object and returns `dict[str, Any]`, catches `RecursionError`, and has tests for the non-UTF-8 and other read-error branches (integration review 6).

## Future work

### Phase 2: pilot in one organisation

**Goal.** Real users, real identities and a real model, operated by one platform team.

| # | Item | Replaces in Phase 1 |
| --- | --- | --- |
| 1 | Single sign-on, with reviewer and submitter roles from directory groups | Stub identities |
| 2 | Managed PostgreSQL with schema migrations | SQLite |
| 3 | Live classifier on an in-region model endpoint. The evaluation gate reruns on every change of model, prompt or threshold | Replay as the default |
| 4 | Human approval required for every server as the default policy | Policy approval of the low tier (already a setting) |
| 5 | Package digest in the submission, and allowed sources narrowed to the internal artifact repository | Fingerprint of manifest and tools only |
| 6 | Withdraw or deprecate an approved version, with a reason and an audit record | No path out of "approved" |
| 7 | Per-version endpoints, search and CORS on the read path | List endpoint only |
| 8 | Export of the approved set as a managed-settings allowlist | No route for clients that do not read a registry, such as Claude Code |
| 9 | Tests against live Amp and Copilot workspaces | Client simulator |
| 10 | Reviewer screen, with the queue listing if it was not delivered as a Phase 1 stretch, notifications and a lead-time metric per submission | Review by CLI with a known submission id |
| 11 | Deployment: write path internal behind single sign-on, read path as a signed static copy at the edge, promotion through environments gated by the same check script. Image scan and a required second reviewer added to the pull request checks. The dependency audit blocks a pull request that introduces a vulnerability, and a scheduled audit raises a ticket for new advisories | Local run only, pull requests merged by their author, an audit that only reports |
| 12 | Audit events streamed to the SIEM and to immutable storage | Audit in the application database |
| 13 | Maximum age and an alert for the degraded list | No expiry |
| 14 | Metrics and dashboards: decisions by outcome, review queue depth, lead time, abstain rate, classifier latency and token use. Traces and metrics go to the organisation's own collector | Logs, and an optional local trace viewer |
| 15 | Dry run for developers: vet a draft without recording a decision or using up the version | Every submission is recorded, and a policy rejection is final for that version |

### Phase 3: assurance at scale

**Goal.** Close the gap between what was approved and what actually runs, and let more than one team set policy.

| # | Item | Replaces |
| --- | --- | --- |
| 1 | Sandbox introspection: start the submitted server in isolation, read its real tool list and compare it with the declaration | Declared tools |
| 2 | Scheduled drift checks of approved versions, and re-vetting when the policy version, prompt or model changes | One vetting per version |
| 3 | Upstream references with a live fetch from a list of trusted registries, if not delivered as a Phase 1 stretch | Recorded upstream responses |
| 4 | More scanner engines as evidence sources, including model judges from third parties | One pattern engine |
| 5 | Policy as code: thresholds and tiers per business unit, changed by pull request and replayed against past submissions before rollout | One global policy from environment variables |
| 6 | Larger evaluation set, fed by real review outcomes, with monitoring of score distribution | About 40 synthetic samples |
| 7 | Loader or gateway integration for agent libraries that have no central setting | Registry-aware platforms only |
| 8 | Evidence export for audits: who approved what, on which evidence, under which policy | Audit read per submission |

## Out of scope

Not planned. Each item either belongs to another control or contradicts a design rule.

| Feature | Why not | Where it belongs |
| --- | --- | --- |
| Inspecting or blocking tool calls at runtime | MCP Greenroom decides before a server is listed and sees nothing at call time | An MCP gateway |
| Detecting a server that was modified on a laptop after approval | A registry cannot see the device | Device management, integrity-pinned installs, or hosting the server centrally |
| Hosting or mirroring server packages | MCP Greenroom holds metadata only | The artifact repository |
| Live links to other registries, or pass-through of their lists | An approved record must not change after approval, and an upstream registry must not sit on the read path | Copy at submission (Phase 1 stretch) |
| Approval by the model alone | Design rule: the classifier can escalate a case and can never clear one | Policy rules and human reviewers |
| Marketplace features: ratings, popularity, browsing | MCP Greenroom is an internal control, not a catalogue | The official registry and public subregistries |
| Source code audit of submitted servers | Vetting covers the manifest and the tool descriptions | Code review and dependency scanning in the owning team's pipeline |
| Per-user authorisation of individual tool calls | A runtime concern | The gateway and the server's own access control |
| Data loss prevention on tool traffic | A runtime concern | The gateway |
| Skills, plugins and other agent extensions that are not MCP servers | A different format and supply chain | A separate intake |

## Keeping this file honest

Update the status table from real output after the build. Move an item between phases only with a line in `evidence/decisions.md` that says why.
