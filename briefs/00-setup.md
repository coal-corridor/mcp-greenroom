# Brief 00: setup

Session: lead. Budget: the first 10 minutes. Lands in the setup pull request, together with brief 10.

## Goal

Before any feature exists, the repo has one check script, pull request checks that call it, and the guard rails that keep the build honest.

## Read first

`docs/specs/mcp-greenroom.md` (the parent) and `docs/specs/delivery.md` in full: it holds the criteria "One check command" and "Pull request checks" and the CI constraints. No other child spec.

## Deliver, one commit each

1. `pyproject.toml` with the stack from the spec and nothing else, a `.python-version` file set to 3.12, an empty `src/mcp_greenroom/` package, and `uv.lock`. Lint rules include the security set. Dev tools sit in a dev group.
2. `scripts/verify.sh`: stages `lint`, `types`, `test`, `eval`, the alias `quick` (lint and types), and no argument for all. It runs every requested stage even after a failure, prints one summary table with result and time per stage, and exits non-zero if any stage failed. Failures lead with what failed and what to do. The `eval` stage is skipped, and says so, until an evaluation set exists: otherwise the setup, registry and edge pull requests could never pass a required check. Commit the script while `test` still fails: that is the honest starting state.
3. A test guard in `tests/conftest.py` that makes any outbound network connection fail, except to localhost. This turns "no network in tests" from a rule into a check.
4. Two structural tests in `tests/structure/`: no source file over 350 lines, and only the config module reads environment variables.
5. `.github/workflows/ci.yml` as the spec describes: parallel jobs for `quick`, `test` and `eval` through the check script, a secret scan over the full history, and a dependency audit that reports and does not block. Read-only permissions, no repository secrets, each action pinned to a commit with the version tag as a comment, the uv version pinned.
6. `Makefile` with `verify`, `run`, `demo` and `record`, each a thin wrapper.

To pin an action, resolve the tag yourself and show the command and its output:

```bash
git ls-remote --tags https://github.com/actions/checkout v7.0.1
```

## The user does, not the agent

- Creates the public repository and pushes.
- Switches off squash and rebase merging.
- After the first run of the workflow, makes the checks required on `main`: `verify (quick)`, `verify (test)`, `verify (eval)` and `secret scan`. The dependency audit stays out of that list.

## Done when

- `./scripts/verify.sh quick` passes, and the full script fails only on `test`, with a clear message, and reports `eval` as skipped.
- The workflow has run once on the pull request and each job is visible by name.
- You have pasted the commands you ran and their output.

## Stop and ask

A dependency outside the stack seems necessary. An action or the uv version cannot be resolved. The audit reports a finding on the first run.
