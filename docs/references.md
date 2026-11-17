# References: MCP Greenroom

Public projects and documents to read for patterns, so the agents do not start each area from a blank page. "Checked" means the page was read on 17 Nov 2026. Everything else is marked (unverified) and needs a look before it is relied on.

## Rules of use

- Read for patterns. Do not copy code, detection rules or sample attacks. The evaluation set is written fresh, with synthetic data. The one exception to "patterns only" is the Cisco scanner, which is used as a pinned package and still not copied.
- Each area brief names at most two references to read first, with the exact path. "Make it like project X" is not an instruction an agent follows well.
- Reading costs build time. Anything read in advance is preparation and is disclosed in `agentic-workflow.md`.
- Keep clones outside the repo, so nothing foreign lands in a commit.
- If code is copied after all, its licence notice goes with it and `agentic-workflow.md` lists the file and the source.
- None of these becomes a dependency without a decision. The stack in the spec is fixed.

## By area

### Registry (API, store, published list)

| Reference | Take from it | Status |
| --- | --- | --- |
| Official MCP registry, `modelcontextprotocol/registry` | Response envelope, cursor paging, real `server.json` examples to model the samples on. Already the source of the pinned OpenAPI document | OpenAPI and schema checked 16 Nov 2026. Licence (unverified) |
| ToolHive Registry Server, `stacklok/toolhive` | How a self-hosted, curated registry is modelled: sources, entries, one API surface. It is also the closest open source prior art, so it belongs in `decisions.md` | Checked: Apache 2.0, implements the official MCP Registry API, signs servers and verifies provenance. Written in Go, so patterns only. No approval step of its own was seen: approval presumably happens in Git (unverified) |
| FastAPI documentation: larger applications, testing with dependency overrides | One package with `main.py`, `dependencies.py` and a `routers` subpackage. Fakes injected in tests through `app.dependency_overrides`, reset after each test | Checked 17 Nov 2026. The guide creates the app at module level and shows no app factory and no `src` layout |

### Vetting (rules, classifier, evaluation)

| Reference | Take from it | Status |
| --- | --- | --- |
| Cisco MCP Scanner, `cisco-ai-defense/mcp-scanner` | The split that MCP Greenroom also uses: fast pattern rules first, then a model acting as judge. Shape of the judge's prompt and of its structured answer. Threat categories for the rule ids | Checked: Apache 2.0, Python, combines YARA rules, LLM-as-a-judge and an optional vendor API. A `static` mode scans a JSON file of tools (name, description, inputSchema) with no running server. The YARA engine needs no key. The judge accepts any LiteLLM-supported model and a custom base URL. Results carry a safe flag, severity and threat names, with no numeric score and no capability tags |
| MCP-Scan by Invariant Labs, `invariantlabs-ai/mcp-scan` | Tool pinning by hash, which is MCP Greenroom's fingerprint. Cross-origin escalation, which is the tool-name shadowing rule | Checked: detects tool poisoning and shadowing, pins tools by hash. Licence (unverified) |
| OWASP MCP Top 10 | Shared names for the risks. MCP03 is tool poisoning, MCP04 is supply chain. Cite them in `design.md` instead of inventing a taxonomy | Existence and the two ids checked through a secondary page. The official list was not read |
| VCR.py and pytest-recording | The record and replay idea MCP Greenroom applies to the classifier: record once, replay on an exact key, fail on a miss | (unverified) |

### Edge (CLI, client simulator, CI, scripts)

| Reference | Take from it | Status |
| --- | --- | --- |
| Spec Kit CLI, `github/spec-kit`, `src/specify_cli` | Typer with Rich, the banner, `Error:` and `Warning:` message style, a `--json` mode | Entry file checked. Selection module and licence not readable when checked |
| questionary | The select prompt for the stretch menu, and its tests for scripted key input | Checked: MIT, one runtime dependency |
| GitHub CLI | Conventions for `--json` output and exit codes | (unverified) |
| Command Line Interface Guidelines, clig.dev | A checklist for help text, errors and output | (unverified) |
| uv documentation for GitHub Actions and the `astral-sh/setup-uv` action | Caching and pinning the uv version in CI | (unverified) |
| GitHub documentation on hardening Actions | Pinning actions to a commit, least-privilege permissions | (unverified) |
| "Scripts to rule them all" | One script as the single entry point for checks | (unverified) |

### Evidence pack

| Reference | Take from it | Status |
| --- | --- | --- |
| Architecture decision records in Michael Nygard's format | Context, decision, consequences: the shape of each record in `decisions.md` | (unverified) |

## Three decisions these references force

1. **Scanner rules as evidence, our own judge for the decision.** MCP Greenroom uses the Cisco scanner's YARA engine as a pinned package, offline and with no key. Its findings are shown as evidence and stop an approval when a rule matches. The model judge stays home-built: thresholds and tiers need a numeric score and capability tags, which the scanner does not return, and the classifier is the AI component the slice exists to show. The scanner's own model judge and the vendor API are not used. Spike at the start of the vetting session, about 20 minutes: run the YARA engine in static mode over the five samples, check that the output can be parsed and that the benign sample has no match. If it does not fit, home-made patterns take its place. Record the outcome in `decisions.md` as a buy-versus-build record.
2. **Why not ToolHive.** Reading on 17 Nov 2026, not confirmed against its documentation: ToolHive has no approval step of its own and presumably leaves approval to Git, where a reviewer merges a change to the catalogue (unverified). It is also a much larger platform: gateway, runtime, operator and registry. MCP Greenroom is the opposite trade: one small service whose whole job is intake, vetting and a recorded decision. In production the read side could well be an existing registry server, with MCP Greenroom's vetting in front of it.
3. **Why a service and not a Git repository with pull requests.** Approval by merge is a legitimate design: the review is the approval, the history is the audit, and branch protection keeps author and approver apart. MCP Greenroom is a service because a developer gets an automated decision inside the request, every decision carries its evidence and policy version in a structured record, and the intake does not depend on where the catalogue is hosted.

## Sources

- https://github.com/modelcontextprotocol/registry
- https://github.com/stacklok/toolhive
- https://docs.stacklok.com/toolhive/guides-registry/intro
- https://github.com/cisco-ai-defense/mcp-scanner
- https://invariantlabs.ai/blog/introducing-mcp-scan
- https://github.com/github/spec-kit
- https://questionary.readthedocs.io/
