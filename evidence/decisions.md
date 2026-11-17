# Decisions: MCP Greenroom

Status: headings only, prepared before the timed build. Three to five records, each added in its own commit when the decision is made, not at the end. The user writes the trade-offs in their own words.

Format of a record: context, decision, consequences.

## Candidates

`TODO(build)`: pick the ones that turned out to matter, and delete this list. Background for each is in `docs/spec-notes.md`, section 2, and `docs/references.md`.

- An approval workflow of our own on the upstream read API.
- Rules before the model. The model can escalate and never clear.
- Replay as the default classifier provider.
- Scanner rules as evidence, our own judge for the decision.
- A last-good copy on the read path.
- A service, not a Git repository with pull requests.
- What was not built on purpose.
- The time split, and what was cut during the build.

## Waive two litellm advisories in the dependency audit

Context: on 2026-11-17, `uv audit` (uv 0.13.8) on the first lock found two advisories in `litellm 1.93.2`: GHSA-g5ff-637f-6q2m (local file read, fixed in 1.95.0) and GHSA-7hp6-4w63-5g45 (privilege escalation to proxy admin, fixed in 1.100.4 and later). `litellm` comes only through `cisco-ai-mcp-scanner` 4.8.7, which pins it exactly (`litellm==1.93.2`), so a bump would override the scanner's own pin. Both advisories are in the LiteLLM proxy server. This project uses only the scanner's YARA engine and never starts that proxy.

Decision (the user's): keep the scanner and waive both IDs under `[tool.uv.audit]` in `pyproject.toml`. After the waiver, `uv audit` reports no known vulnerabilities in 118 packages, exit 0. Not chosen: dropping the scanner, overriding `litellm`, or leaving both advisories open.

Consequences: the vulnerable code still ships in the environment, unused. The waiver hides these two IDs only, and any new advisory still shows. The audit job stays in CI. Production route: remove the waiver once a scanner release unpins `litellm` at a fixed version, or vendor only the YARA rules and drop the package.

## What I read line by line

`TODO(build)`: which paths the user reviewed line by line (validation, config, error handling, the decision order) and which were accepted on passing checks.

## Harness choices

`TODO(build)`: what the agent setup included and what it left out, and why.
