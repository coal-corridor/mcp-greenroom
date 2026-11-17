# Spec notes: MCP Greenroom

Background for `docs/specs/mcp-greenroom.md`: research facts, rationale and production routes. Nothing here is needed to build the slice. Read it when writing `design.md`, `decisions.md`, `operate.md` and `verify.md`.

Every fact carries the date it was checked. Platform behaviour was read from public documentation and never tested against a live product.

## 1. Registry and platform facts

Checked on 16 Nov 2026 unless a line says otherwise.

- The MCP project runs one official registry and expects private subregistries inside enterprises that speak the same API. MCP Greenroom is such a subregistry, filled by its own vetted submissions instead of a sync from upstream.
- The upstream registry API has no approval step (OpenAPI `info.version` 2025-12-01). The write side of MCP Greenroom is its own workflow, not the upstream publish API.
- The upstream list returns one record per server version and pages with a cursor. Server names contain a slash.
- Fetched on 16 Nov 2026: the `server.json` schema 2025-12-11 has no field for tool definitions. Its package `registryType` is a free string (examples given: npm, pypi, oci, nuget, mcpb). The OpenAPI path list has no endpoint for referencing a server in another registry.
- Amp blocks every server when its registry is unreachable, which is why degrade mode exists. Amp matches package name and registry type, not version, so per-version approval is exact inside MCP Greenroom and a stated limit at the enforcement point.
- Copilot's registry enforcement is in public preview and needs the per-version endpoints and CORS. Its recommended control, like Claude Code's, is a managed-settings allowlist.
- A registry is optional to the protocol. It becomes a control only when an admin switches on host-side enforcement. The MCP client and protocol know nothing about registries: the host checks before it creates a client for a server.

## 2. Rationale, for `decisions.md`

- **Own approval workflow on the upstream read API.** The upstream API has no review step, and the platforms only read the list. Alternatives to record: ToolHive Registry Server (open source, implements the official registry API, checked 17 Nov 2026), API7 AISIX, Azure API Center, Cisco mcp-scanner. `references.md` has the two questions these raise.
- **Rules before the model.** The classifier can escalate a case and can never clear one. A provider failure or a missing recording sends the case to a human.
- **Scanner rules beside the model.** An established open source rule set gives a second, independent signal and names its findings in a published taxonomy. It can stop an approval and never grant one, so a false match costs a review, not a wrong approval. The model judge stays home-built because the scanner returns no score and no capability tags.
- **Replay as the default provider.** Assessors run the slice with no key and no network, and get the same answers every time. A recording is real model output, kept per tool. In real use the provider is switched to live.
- **Recordings through the API, not through a headless coding agent.** A bare model call has no tools, so a poisoned sample cannot make the recorder act. An agent harness would have to be stripped of its tools first.
- **What the evaluation proves.** It replays recordings, so it guards the decision logic and the recorded model behaviour. It says nothing about a different model or a changed prompt. Either change means recording again.
- **Copy, not link, for upstream references.** A live reference could change after approval, which breaks immutable versions. It would also put the upstream registry on the read path that Amp treats as all-or-nothing.
- **The dependency audit reports and does not block.** It is the one check that can turn red with no change in the repo, because it depends on an external advisory list.
- **One pull request per area, merge commits only.** One per change would spend the timebox waiting for CI. Squash and rebase merging rewrite history, which the exercise forbids.
- **CLI first, menu second.** The demo script, the tests and CI need commands that never prompt. The menu adds no capability: each item calls the same function as a command.
- **Inert printing of untrusted text.** A tool description can carry terminal control characters or markup. The reviewer's terminal is part of the attack surface.

## 3. Production routes, for `design.md` and `operate.md`

`ROADMAP.md` holds the full list. These are the routes the spec refers to.

- **Packages.** MCP Greenroom holds metadata only. Packages stay where the manifest points: npm, PyPI or an OCI registry, or a remote server on an https URL. In the slice the sample packages do not exist, and nothing is fetched or started. In production the pointers resolve to the internal artifact repository, the allowed-source rule is narrowed to those hosts, and a submission carries a package digest so that an approval is bound to the artifact. Today the fingerprint covers the manifest and the tool definitions only.
- **Dependency audit.** Block a pull request only on a vulnerability that the change itself introduces, and run a scheduled audit that raises a ticket for new advisories.
- **Delivery.** Nothing is deployed in the slice. Promotion through environments is gated by the same check script that runs locally and in CI.
- **Clients that do not read a registry.** Export the approved set as a managed-settings allowlist (Claude Code, and Copilot's recommended control).
- **Withdrawal.** The slice has no way to withdraw an approved version. Phase 2 adds it.

## 4. Tooling facts

Checked on 17 Nov 2026 unless stated.

- `uv audit` exists from uv 0.10.12, reads the lockfile, queries OSV and exits non-zero on a finding. Ignores go in `[tool.uv.audit]`. It is a preview command whose interface may change: in uv 0.11 and 0.13 it prints an "experimental" warning, takes `--locked`, and can write text, JSON or SARIF. The name of the preview flag that silences the warning differs between sources, so CI does not pass one.
- Resolved on 17 Nov 2026 for the CI workflow: uv 0.13.8, `actions/checkout` v7.0.1, `astral-sh/setup-uv` v10.3.3, `gitleaks/gitleaks-action` v3.0.0. Resolve them again when the workflow is written.
- The official gitleaks action needs a licence key for a repository owned by an organisation account and none for a personal account. The repository is under a personal account.
- The Cisco MCP Scanner (`cisco-ai-mcp-scanner`) is Apache 2.0. Its `static` mode scans a JSON file of tools (name, description, inputSchema) with no running server. The YARA engine needs no key. Its model judge accepts any LiteLLM-supported model and a custom base URL, and is not used here. Results carry a safe flag, severity and threat names, with no numeric score and no capability tags.
- questionary is MIT licensed, with one runtime dependency, prompt_toolkit. Its select prompt uses the arrow keys by default, and its own tests drive it with scripted key input.
- Typer depends on Rich: a lockfile resolved on 17 Nov 2026 for a project that adds only Typer contains Rich.
- The Spec Kit licence was not checked, because the page could not be fetched. This matters only if code is copied.
- Cost of one recording run, an estimate: about 55 calls, about 50,000 tokens in and 11,000 out. At list prices read from secondary pages (Haiku 5.5 at $0.10 and $0.50 per million tokens, Sonnet 5.5 at $2 and $10, Opus 5.5 at $4 and $20) that is between one cent and about 40 cents. Extended thinking is billed as output and would raise it. Confirm prices on the official page.

## 5. CLI references

Read on 17 Nov 2026 for patterns. Nothing is copied.

- Spec Kit CLI (`src/specify_cli`): Typer with Rich, a banner on the bare command, a step tracker, a red `Error:` and a yellow `Warning:` prefix with a follow-up line, a `--json` mode, arrow-key selection through a small key reader.
- An article on designing for the command line (yannglt.com): status symbols, the basic ANSI palette, no assumption about the user's theme, tabular layout, a design for each state. The "Specify CLI" it describes appears to be a different product from Spec Kit's `specify` (unverified).

## 6. Sources

- https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/api/openapi.yaml
- https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json
- https://blog.modelcontextprotocol.io/posts/2025-09-08-mcp-registry-preview/
- https://modelcontextprotocol.io/community/registry/charter
- https://pydevtools.com/handbook/how-to/how-to-scan-python-dependencies-for-vulnerabilities/
- https://github.com/marketplace/actions/gitleaks
- https://questionary.readthedocs.io/en/latest/pages/types.html
- https://github.com/github/spec-kit/blob/main/src/specify_cli/__init__.py
- https://yannglt.com/writing/designing-for-command-line-interface
- https://platform.claude.com/docs/en/about-claude/pricing
