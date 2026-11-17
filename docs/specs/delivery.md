# Spec, child: delivery

Read the parent first: `docs/specs/mcp-greenroom.md`. This file adds what the
lead session must deliver at setup and prove at integration: the check command
and the pull request checks.

### Acceptance criteria

- [ ] **One check command.** `./scripts/verify.sh` runs lint, type check, tests
and the evaluation, prints pass, fail or skip per stage and exits non-zero if
any stage failed. It passes with no network and no credentials. Given a stage
name (`lint`, `types`, `test`, `eval`, or `quick` for lint and types) it runs
that stage alone, so CI runs the same script as parallel jobs. Until an
evaluation set exists in the tree, the `eval` stage says so and is skipped, not
failed. From then on it is a gate.
- [ ] **Pull request checks.** A GitHub Actions workflow runs on every pull
request and every push to `main`, as parallel jobs: the stages of
`./scripts/verify.sh` (lint and types, tests, evaluation), a secret scan over
the full history and a dependency audit of `uv.lock`. All jobs are required for
a merge except the audit, which runs from the first pull request and reports
without blocking. No repository secrets, read-only permissions, each action
pinned to a commit. Proof: the required checks on the last commit of `main` are
green and linked from `evidence/verify.md`, which also states the audit
result.

### Build constraints

- CI-only tools, neither a dependency of the application: `uv audit` (a preview
command, so CI pins the uv version) and the official gitleaks action (no
licence key is needed under a personal account).
- Every audit finding is listed in `verify.md` with what was done: package
bumped, waived in `[tool.uv.audit]` with a record in `decisions.md`, or left
open. The audit job is never deleted.
- Nothing is deployed, so there is no CD stage. `design.md` and `operate.md`
describe promotion, with the same check script as the gate.
- Changes reach `main` through pull requests: one for setup, one per area
(registry, vetting, edge) and one for integration. Each is merged with a merge
commit once the required checks are green. Squash and rebase merging are
switched off in the repository, because both rewrite history.
