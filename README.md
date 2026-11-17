<h3 align="center">
MCP Greenroom: vetted registry for MCP servers
</h3>

## What is MCP Greenroom?

MCP Greenroom is a self-managed MCP registry with a built-in validation and approval pipeline.
It provides an in-house intake and risk review for MCP servers, and publishes the approved list in the registry for coding agents and development environments.

## Why MCP Greenroom?

An MCP server gives a coding agent new tools, and the agent reads each tool's description as instructions. A poisoned description is an attack path. A regulated enterprise must be able to control what MCP servers are available for the developers via a curated registry, with a submission approval process, evidence, and policy.

## How it works

A developer submits one version of a server with its tool list. MCP Greenroom then:

1. validates the submission and applies deterministic rules (pinned version, allowed package source, no hidden characters);
2. runs scanner rules and has a classifier score each tool description for injection risk and tag its capabilities;
3. rejects the version, approves it by policy, or sends it to a human reviewer, who can never be the submitter;
4. publishes approved versions on `GET /v0.1/servers` in the official MCP registry format, so a platform that reads a registry enforces the list with no custom code.

```text
submit -> validate -> rules -> scanner -> classifier -> decide -> (human review) -> publish -> GET /v0.1/servers
```

Rules run before the classifier, and the classifier can escalate a case but never clear one. Every decision leaves an append-only audit record. By default the classifier replays recorded model responses, so the workflow and every check run from a clean checkout with no credentials and no network.

## Prerequisites

`TODO(build)`: what a fresh machine needs, as tested from a clean clone.

## Setup

`TODO(build)`

## Run

`TODO(build)`

## Check

`TODO(build)`: the one command, and what its output looks like.

## Example workflow

`TODO(build)`: one real run of the main path, with input and output.

## Known limitations

`TODO(build)`: from what was built. See also `ROADMAP.md`.

## Evidence

The evidence pack is in [`evidence/`](evidence/): `intent.md`, `design.md`, `agentic-workflow.md`, `verify.md`, `operate.md`, `decisions.md`. The spec the slice was built against is [`docs/specs/mcp-greenroom.md`](docs/specs/mcp-greenroom.md), with one child spec per area in [`docs/specs/`](docs/specs/). The roadmap is [`ROADMAP.md`](ROADMAP.md).

## Where things are

`TODO(build)`: one line per top-level folder, so a reader finds the code, the tests, the samples and the evidence in a minute.

## Third-party components

`TODO(build)`: each dependency that shapes a decision, with its licence. If the scanner rules are in, name the Cisco MCP Scanner (Apache 2.0) here.
