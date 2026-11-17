# Spec, child: edge

Read the parent first: `docs/specs/mcp-greenroom.md`. Its decision order,
invariants and scope apply here unchanged. This file adds what only the edge
area must deliver: the CLI and the client simulator.

### Acceptance criteria

- [ ] **Client check.** A client simulator follows Amp's documented check: it
reads a sample MCP client config, matches each local server on package name and
registry type, allows the listed one and blocks the unlisted one. With the
registry unreachable it blocks both.
- [ ] **CLI.** The `mcp-greenroom` commands drive every step of the demo over
HTTP and follow the CLI section below. Tests cover the exit codes, the `--json`
output of `submit`, plain output when piped, and one description that carries
markup and control characters and is printed inert.

### CLI

There is no screen in this slice. The CLI is the interface for the developer,
the reviewer and the demo. It talks to the API over HTTP only. Typer builds the
commands and Rich renders the output.

Commands:

- `mcp-greenroom submit FILE`: sends one server version for vetting. Shows the
decision, tier, reasons, a table of findings and the offending text.
- `mcp-greenroom status ID`: shows a submission in the same view.
- `mcp-greenroom review ID --approve` or `--decline`, with `--note TEXT`:
records a human decision.
- `mcp-greenroom audit ID`: lists the audit records: time, actor, action,
reasons, policy version.
- `mcp-greenroom list`: lists the approved versions from the registry endpoint,
with a warning line when the registry is degraded.
- `mcp-greenroom client-check CONFIG`: runs the client simulator. One line per
server: allowed or blocked, and why.
- `mcp-greenroom health`: liveness, readiness and registry mode, one line each.

Conventions:

- The API address comes from `--api` or `MCP_GREENROOM_API`, the identity from
`--token` or `MCP_GREENROOM_TOKEN`. Every command has `--help` with one example.
- A status is always a symbol and a word: `✓ approved`, `! needs review`,
`✗ rejected`. Colour only repeats it: basic terminal colours, no background
colour, no assumption of a dark or a light theme. No colour and no spinner when
the output is not a terminal or `NO_COLOR` is set.
- `--json` prints one JSON document, the API response body, and nothing else on
standard output.
- No prompts. Everything a command needs is an argument or an option.
- Results go to standard output, errors to standard error. An error has three
parts: what failed (with the rule id from the API), what was received, what to
do next. No stack trace unless `--debug` is given.
- After a result, one dim line names the next step.
- Untrusted text (tool names, descriptions, evidence, notes) is printed inert:
no markup is interpreted, and control and hidden characters are shown escaped.
- Bare `mcp-greenroom` prints the name, a tagline and the command list.

Exit codes:

- 0: done. For `submit` and `status`, approved. For `client-check`, every
server allowed.
- 1: operational failure: API unreachable, server error, not authenticated.
- 2: usage error (the framework default).
- 10: in human review.
- 20: rejected or refused: validation refusal, policy rejection, conflict,
forbidden review. For `client-check`, at least one server blocked.

Cut first: `health`, `audit`, the spinner, the tagline. Never cut: `--json`,
the exit codes and inert printing. The demo script and the tests rely on them.

Not in this CLI: shell completion and a config file. An interactive menu and a
listing of the cases waiting for review are a stretch item, defined in
`stretch.md`.
