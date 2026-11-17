# Brief: edge area

Session: its own worktree, branch `area/edge`. Starts third, once the API shape has held. One pull request.

## Goal

A person clones the repo, runs one command to check it and one to see the whole workflow, and drives every step from the `mcp-greenroom` command.

## Owns

`src/mcp_greenroom/cli.py`, `src/mcp_greenroom/cli_output.py` (added 2026-11-17 with the user's agreement, for the 350-line limit), `src/mcp_greenroom/client_sim.py`, `scripts/demo.sh`, `tests/e2e/`, `sample-data/client-configs/`, `Dockerfile`, `docker-compose.yml`, `deploy/README.md`. Nothing else. `scripts/verify.sh` and the workflow change only with the user's agreement.

## Read first

`docs/specs/mcp-greenroom.md` (the parent: decision order for the outcomes, invariants, definition of done), then `docs/specs/edge.md` in full. No other child spec. From `docs/references.md`, at most the Spec Kit CLI entry file for message style.

## Deliver

1. The `mcp-greenroom` commands in the spec, over HTTP only: `submit`, `status`, `review`, `audit`, `list`, `client-check`, `health`.
2. The conventions: symbol and word for status, no colour when piped or with `NO_COLOR`, `--json` printing the unchanged response, no prompts, three-part errors, a next-step line, and the exit codes.
3. Inert printing of untrusted text, with a test that feeds markup and control characters.
4. The client simulator: reads a sample client config, matches on package name and registry type, allows the listed server, blocks the rest, and blocks everything when the registry is unreachable. Label it as a simulation of documented behaviour.
5. `scripts/demo.sh`: starts the service, walks the main path and the five safe failures, prints each result, and stops the service.
6. One end-to-end test that drives the main samples through the real app. Until the other areas are merged, test against the fake from the contracts step.
7. Container files, and `deploy/README.md` with the production shape in words only.

## Tests to write first

Exit code per outcome. `--json` output of `submit` equals the API body. Plain output when piped. The inert-printing case. The client simulator's three situations.

## Done when

`./scripts/verify.sh quick` and this area's tests pass, and `./scripts/demo.sh` runs end to end against the fake.

## Cut first

`health`, `audit`, the spinner, the tagline, then the container files. Never `--json`, the exit codes or inert printing.

## Stop and ask

A command needs an endpoint the spec does not list. Rich or Typer cannot do something without one more dependency.
