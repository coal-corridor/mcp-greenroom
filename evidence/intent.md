# Intent: MCP Greenroom

Status: draft, written before the timed build. Platform claims checked against vendor documentation on 16 Nov 2026.

## Problem

An MCP server gives a coding agent new tools, and the agent reads each tool's description as instructions. A poisoned description is therefore an attack path. A regulated enterprise must be able to say who approved a server, on what evidence and under which policy.

Agent platforms enforce an approved list but leave its content to the customer:

- **Amp.** An enterprise workspace admin enters a registry URL (the `v0.1/servers` endpoint of the MCP registry API). Amp blocks every server not listed, and blocks all servers when the registry is unreachable.
- **GitHub Copilot.** Accepts a custom registry on the same v0.1 API with a "Registry only" policy. GitHub marks this as a public preview and recommends an allowlist in `managed-settings.json` as the more secure control.
- **Claude Code.** Takes an allowlist in managed settings (`allowedMcpServers`). It does not read a registry.

None of these decides what belongs on the list. The upstream registry API defines publish and status endpoints, with no review or approval step.

MCP Greenroom is that missing step: an in-house intake and risk review for MCP servers, which publishes the approved list in the registry format the platforms read. The route must be fast and predictable, because developers work around a control that is slow.

## Intended users

- **Developer.** Submits one version of a server and gets a decision with its reasons.
- **Reviewer** (platform or security). Decides the cases that policy could not, with a note. Never reviews their own submission.
- **Agent platform.** Reads the approved list and asks one question: is this server on it?

## Assumptions

- Vetting happens once per server version, at submission, before listing. Nothing is inspected when an agent calls a tool.
- The slice judges the tools a submitter declares, not what the running server exposes.
- Tool descriptions are untrusted input, including towards the classifier that scores them.
- A model is useful for scoring descriptions and is not trusted to approve. Rules run first. The model can escalate a case and can never clear one that a rule has stopped.
- Low-risk servers may be approved by policy, so the demo shows all three outcomes. A bank would likely require a human for every server. That is a policy setting, not a redesign.
- Platform behaviour is taken from public documentation and simulated. Nothing is tested against the live products.

## Constraints

- Built in a three-hour timebox with Claude Code as the primary implementation tool. Commits are incremental and history is never rewritten.
- The core path runs from a clean checkout with no paid API keys, no private credentials and no model call: by default the classifier replays recorded responses.
- Synthetic data only: invented servers under one fictional organisation.
- One command runs every check expected in CI.
- Fail closed. When a result is uncertain or a component is unavailable, the submission goes to a human.

## Out of scope

- Starting a submitted server in a sandbox to observe its real tools.
- Runtime traffic inspection. That is a gateway's job.
- Detecting a server that was modified on a laptop after approval.
- Drift checks after approval. Each version is approved separately.
- Single sign-on, a reviewer screen, a production database and any cloud deployment.
- The full registry API. The slice serves the list endpoint. The per-version lookups that Copilot requires are a stretch item.

## Success criteria

Each one can be checked by an assessor from a clean checkout.

1. **Main workflow.** A benign sample server is submitted, vetted, approved and listed on the registry endpoint. A client simulator then allows it and blocks an unlisted server.
2. **Standard format.** The registry response validates against the official MCP registry OpenAPI schema.
3. **Five safe failures**, each shown by the demo script and covered by a test:
   - a malformed submission is refused with a clear error (validation rejection);
   - a poisoned tool description is rejected with the reason and the evidence (guarded failure);
   - an input the classifier cannot judge goes to human review (abstain);
   - a submitter cannot approve their own server (separation of duties);
   - with the store down, the registry endpoint serves the last good list and reports that it is degraded (degrade mode).
4. **Classifier evaluation.** A labelled synthetic set runs inside the check command. Hard gate: no malicious sample is auto-approved.
5. **One check command** passes with no network access and no credentials.

Invariants that hold on every path:

- No server is approved when a rule has stopped it, or when the classifier failed or abstained.
- Only approved servers appear on the registry endpoint.
- Every decision leaves an append-only audit record: who, what, when, why and which policy version.
