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

## What I read line by line

`TODO(build)`: which paths the user reviewed line by line (validation, config, error handling, the decision order) and which were accepted on passing checks.

## Harness choices

`TODO(build)`: what the agent setup included and what it left out, and why.
