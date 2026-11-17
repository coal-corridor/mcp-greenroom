    Status: Draft
    Last updated: 2026-11-17

# Spec: MCP Greenroom, vetted intake for MCP servers

### Goal

Build a self-hosted MCP registry with a vetting pipeline, so that the
organisation controls in one place which MCP servers its coding agents may use,
and every decision is recorded with who made it and why. A developer submits a
specific version of a server to MCP Greenroom. MCP Greenroom validates it,
applies rules, has a classifier score each tool description, then rejects it,
approves it or sends it to a human reviewer. Approved versions are published in
the official MCP registry format, so agent platforms that read a registry
enforce the list with no custom code.

### Child specs

This file is the parent. Each child in `docs/specs/` holds what one area must
deliver. A child never overrides the parent: if the two disagree, stop and ask.

- `vetting.md`: criteria Guarded failure, Abstain and Classifier evaluation.
Tier definitions and thresholds. Constraints for the scanner rules and the
recordings.
- `registry.md`: criteria Standard format, Separation of duties, Degrade mode,
Audit and Operability. The pinned upstream documents.
- `edge.md`: criteria Client check and CLI. The CLI section.
- `delivery.md`: criteria One check command and Pull request checks.
Constraints for CI and for pull requests.
- `stretch.md`: tracing, the interactive menu and submission by upstream
reference. Not part of the committed slice.

### Acceptance criteria

Each criterion is checked by a test. Named samples are synthetic servers under
`com.examplebank`, kept in `sample-data/`.

The three below span more than one area. The other twelve are in the children,
as listed above. All fifteen count for the definition of done.

- [ ] **Main path.** Submitting `payments-readonly` 1.2.0 (benign, read-only
tools) returns "approved by policy", tier low, with reasons, inside the request
and in under 5 seconds locally. The version then appears on `GET /v0.1/servers`.
- [ ] **Validation rejection.** Submitting `invalid-unpinned` (version `latest`)
is refused with 422, a stable rule id and a readable message. No stack trace,
nothing listed.
- [ ] **Immutable versions.** The fingerprint covers the manifest and the tool
definitions. Resubmitting identical content returns the existing decision. Any
other content under a name and version that already has a stored decision is
refused with 409, whatever that decision was. A 422 refusal stores no decision.

### Decision order

First match wins. The tier comes from the capability tags the classifier
returns for each tool.

1. Malformed, version not pinned, package source not allowed, or no tools:
refused with 422.
2. Hidden characters in a name or description: rejected.
3. Classifier unavailable, or no recording for a tool: human review.
4. Highest risk score at or above the reject threshold: rejected.
5. Highest risk score at or above the approve threshold: human review.
6. A scanner rule matched on any tool: human review.
7. Tier medium or high: human review.
8. Tier low: approved by policy, or human review when policy demands a human
for every server.

Scanner findings are shown with every outcome, as evidence beside the
classifier's result.

A reviewer approves or declines a case in human review. A rejection is final:
the fix is a new version.

The tier definitions and the threshold values are in `vetting.md`.

### Invariants

These hold on every path, including the ones no criterion names.

- Policy never approves a version that a rule has stopped, or whose classifier
result failed, was missing or was uncertain (a score at or above the approve
threshold). The classifier can push a case to review or rejection. It can never
clear one.
- Scanner rules can stop an approval. They never grant one, and never reject on
their own.
- Only approved versions appear on the registry endpoint, as upstream-format
server records. Nothing MCP Greenroom produced is published: no scores,
evidence, reviewer notes or audit records.
- A reviewer is never the submitter. The check compares identities, not roles.
Identity comes from the caller's credential, never from the request body.
- Audit records are append-only. Every decision carries the policy version that
produced it.
- Tool names and descriptions are untrusted data, never instructions. Logs
carry their hashes, not their text.
- Tests, the check command and the default run make no network call and need no
credential. By default the classifier replays recorded responses.
- Synthetic data only. No secrets in the repo.

### In scope

- Submit, status, review and audit read over HTTP. Identities are stubs that
work only in the dev environment: all three may submit, two are reviewers.
- Vetting as in the decision order. The classifier sits behind a swappable
interface: replay by default, a live model on a configurable endpoint as an
option. Scanner rules (the YARA engine of the Cisco MCP Scanner, offline, no
key) run on every submission and add findings as evidence.
- The registry list endpoint, with a last-good copy to fall back on.
- CLI, client simulator, demo script, check script, CI workflow, container
files.
- Evaluation set, recordings, README, evidence pack.

### Cut order

- Stretch, built only when everything else is green: tracing, submission by
upstream reference, the interactive menu (these three are defined in
`stretch.md`), the per-version lookup endpoints, a rule for tool names that
shadow an approved server.
- Cut in this order when behind: the five stretch items as listed, then the
scanner rules, container files, CLI commands the demo does not use, the type
check stage.
- Never cut: the check script, the three outcomes (approved, human review,
rejected) end to end, degrade mode, the evaluation gate, the evidence pack.

### Out of scope

- Starting a submitted server to observe its real tools. Runtime traffic
inspection. Drift or local modification after approval.
- Live references to upstream records, pass-through of another registry's list
and scheduled sync from upstream. An approved record is a copy.
- Hosting or mirroring packages, and binding an approval to the package bytes.
- Single sign-on, a reviewer screen, a production database, queues, any cloud
deployment.
- Exporting the approved set as a managed-settings allowlist for Claude Code
and Copilot. `design.md` describes it as the production route.
- Tests against live Amp or Copilot.
- A dry run that vets a submission without recording a decision.

At the wall: if a criterion seems to need one of these, a new dependency, or a
departure from the vendored upstream documents, stop and ask. Do not build
around it.

### Definition of done

- [ ] `./scripts/verify.sh` is green in a fresh clone.
- [ ] The required pull request checks are green on the last commit of `main`.
- [ ] The demo script shows the main path and the five safe failures
(validation rejection, guarded failure, abstain, separation of duties, degrade
mode), and its real output is saved in `evidence/verify.md`.
- [ ] The README states what the solution does, prerequisites, setup, the run
command, the check command, one example workflow, known limits and where the
evidence is.
- [ ] `evidence/` holds `intent.md`, `design.md`, `agentic-workflow.md`,
`verify.md`, `operate.md` and `decisions.md`, one page each, written from real
output, naming the known gaps and the production route for each shortcut.
- [ ] No `TODO(build)` marker is left in the repo.
- [ ] History is incremental and never rewritten.
- [ ] For each criterion, in this file and in the children, the agent states
whether it is met and names the test that proves it.

### Stack and build constraints

- Stack is fixed: Python 3.12 (pinned in `.python-version`), uv, FastAPI served
by uvicorn, Pydantic v2, pydantic-settings, SQLAlchemy 2 (sync) on SQLite,
Typer, Rich, httpx, jsonschema, PyYAML, pytest, ruff, mypy. The Cisco MCP
Scanner package (`cisco-ai-mcp-scanner`, Apache 2.0) is allowed for its YARA
engine only: its model judge and the vendor API are not used. A stretch item
names its own extra dependency in `stretch.md`. Anything else: stop and ask.
- Reference projects are read for patterns and not copied. `docs/references.md`
lists them by area, with what to take from each. Each area brief names at most
two to read first. Copied code keeps its licence notice and is listed in
`agentic-workflow.md`.
- `docs/spec-notes.md` holds the research facts, the rationale and the
production routes. It is not needed to build. Read it when writing `design.md`,
`decisions.md`, `operate.md` and `verify.md`.
