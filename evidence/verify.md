# Verification: MCP Greenroom

Results are from commands run on 17 Nov 2026. Full, unedited output is in [`raw/`](raw/) and in the files linked.

## Checks run and results

| Check | Result | Detail |
| --- | --- | --- |
| `./scripts/verify.sh` in a fresh clone: lint, types, tests, evaluation gate | All four stages pass, 436 tests | Block below |
| `./scripts/demo.sh` | Exit 0. All 14 steps gave the expected exit code | [`raw/demo.txt`](raw/demo.txt) |
| Break test from a fresh clone: missing config, bad input file, store stopped | No stack trace. Two unclear messages found and fixed test first | [`raw/break-test.txt`](raw/break-test.txt) |
| Pull request checks, five jobs | Green on the last commit of every merged pull request | "Pull request checks" below |
| Independent agent review, four runs, and `/security-review` | 43 findings, 6 High, all six fixed. No vulnerabilities reported | "Independent review" below |
| Manual smoke test from a fresh clone, after the build | Core path, safe failures and audit trail as specified. Three cosmetic issues | "Known gaps" below |

Check script, fresh clone at `546c2fb`, following the README's Setup section. uv 0.13.8, Python 3.12.3, WSL 2 on Ubuntu 24.04. Excerpt:

```text
436 passed in 20.20s

verify summary
  stage  result time
  lint   pass   0.1s
  types  pass   5.4s
  test   pass   23.8s
  eval   pass   3.2s

verify: all requested stages passed or were skipped.
```

Tests by folder: structure 18, shared 29, unit 258, api 44, contract 3, failure 14, e2e 70.

## Acceptance criteria

| Criterion | Met | Proof |
| --- | --- | --- |
| Main path | Yes | `tests/api/test_pipeline_wiring.py` |
| Validation rejection | Yes | `tests/api/test_refusal.py` |
| Immutable versions | Yes | `tests/api/test_resubmission.py`, `tests/shared/test_fingerprint.py` |
| Guarded failure | Yes | `tests/unit/test_decision_order.py`, `tests/contract/test_server_list.py` |
| Abstain | Yes | `tests/unit/test_factory.py`, `tests/unit/test_decision_order.py` |
| Classifier evaluation | Yes | The `eval` stage, `tests/unit/test_eval_gate.py`, `tests/unit/test_eval_dataset.py` |
| Standard format | Yes | `tests/contract/test_server_list.py` |
| Separation of duties | Yes | `tests/api/test_review.py` |
| Degrade mode | Yes | `tests/failure/test_degrade.py` and two more files in `tests/failure/` |
| Audit | Yes | `tests/api/test_audit.py` |
| Operability | Yes | `tests/api/test_operability.py`, `tests/failure/test_startup_pipeline.py` |
| Client check | Yes | `tests/e2e/test_client_sim.py` |
| CLI | Yes | `tests/e2e/test_cli.py`, `test_cli_submit.py`, `test_cli_commands.py`, `test_e2e.py` |
| One check command | Yes, by run | No test covers `verify.sh`. Shown by the run above and by CI |
| Pull request checks | Partly | All five jobs green. No check is marked required yet |

## Classifier evaluation

The `eval` stage replays 47 recordings from `claude-haiku-5-5`, prompt `classifier-v1`, with `cisco-ai-mcp-scanner` 4.8.7 beside it. The 41 per-case rows are in [`evals/report.md`](../evals/report.md).

| Label | Total | Approved | Human review | Rejected | Scanner matched |
| --- | --- | --- | --- | --- | --- |
| benign | 18 | 15 | 3 | 0 | 0 |
| malicious | 16 | 0 | 0 | 16 | 6 |
| ambiguous | 7 | 0 | 7 | 0 | 0 |

- Gate: pass. No malicious case was approved, and 24% of cases went to review, under the 50% cap.
- The scanner matched 6 malicious cases. All six were already rejected on score, so it changed no outcome in this set.
- The first recording run, on `claude-opus-5-5` (`827782a`), refused 17 of 47 tools. Every refusal went to human review and none was approved. The Haiku recordings (`66567b5`) replaced it.

## Demo: the main path and five safe failures

| Scenario | Outcome |
| --- | --- |
| Main path | `payments-readonly` 1.2.0 approved by policy at tier low, listed, and allowed by the client check |
| 1. Validation rejection | `invalid-unpinned` refused, 422 `validation.version_not_pinned` |
| 2. Guarded failure | `poisoned-notes` rejected at score 0.97, with two scanner findings as evidence |
| 3. Abstain | `unrecorded-reporter` sent to human review, `classifier.no_recording` |
| 4. Separation of duties | The submitter's own review refused, 403 `review.reviewer_is_submitter`. A second reviewer approved. The audit trail shows who decided, under which policy version |
| 5. Degrade mode | Store broken: the last-good list is served with a warning, health reports not ready, a submit is refused with 503 |

## Pull request checks

- Five jobs on every pull request and every push to `main`: `verify (quick)`, `verify (test)`, `verify (eval)`, `secret scan` (gitleaks 8.30.1, full history) and `dependency audit` (reports, never blocks).
- Two red runs on the way, both fixed before the merge: pull request 3 (Typer colour under `GITHUB_ACTIONS`, `500774a`) and pull request 4 (47 false positives on the replay keys, allowlisted in `eedd2ca`).
- Two advisories in `litellm 1.93.2` are waived in `[tool.uv.audit]`, with a record in `decisions.md`.
- Not enforced during the build: the repository was private, so no check was marked required, and the user merged each pull request by hand on green.

## Independent review

A read-only reviewer agent with a fresh context, given the spec and the diff. It read the code and ran nothing.

| Area | Findings | High | Fixed | Report |
| --- | --- | --- | --- | --- |
| registry | 13 | 2 | 7 | [`registry-review.md`](../handoff/registry-review.md) |
| edge | 11 | 1 | 5 | [`edge-review.md`](../handoff/edge-review.md) |
| vetting | 13 | 3 | 9 | [`vetting-review.md`](../handoff/vetting-review.md) |
| integration | 6 | 0 | 3, and a lock for one point not verified | [`integration-review.md`](../handoff/integration-review.md) |

The rest were deferred to `ROADMAP.md` or accepted, each with a recorded decision. No finding was judged wrong. `/security-review` on the integration diff reported no vulnerabilities. `/code-review` was not run, cut for time.

## Local, pull request, pipeline

| Check | Local | Pull request | Later pipeline |
| --- | --- | --- | --- |
| Lint and types | `./scripts/verify.sh quick`, and the `Stop` hook after each agent turn | `verify (quick)` | Same script at each promotion |
| Tests | `./scripts/verify.sh test`, and the `Stop` hook | `verify (test)` | Same script |
| Evaluation gate | `./scripts/verify.sh eval` | `verify (eval)` | Rerun on every change of model, prompt or threshold |
| Secret scan | Not run locally | `secret scan` | Same |
| Dependency audit | Not run locally | Reports, never blocks | Blocks a pull request that adds a vulnerability |
| Image scan, second reviewer | None | None | Planned, `ROADMAP.md` Phase 2, item 11 |

## Known gaps

Routes for these are in `ROADMAP.md`.

- The evaluation replays recordings from one model and one prompt. It guards the decision logic, not the model's accuracy in general.
- The 41 cases are synthetic, written by the same people and agents who wrote the rules.
- The agent reviewer read code and ran nothing, and `/code-review` was not run.
- Shell settings are read when the app module is imported, so test collection sees a local `.env` or exported `MCP_GREENROOM_*` variables.
- Scanner thread safety is not verified. A lock runs one scan at a time.
- Inert text wraps across two lines in narrow terminals (measured at 64 and 60 columns; 80 and 120 were fine). It is still printed as text.
- No test covers `verify.sh` or `ci.yml`.
- Checks were not required during the build.
- Two non-default policies can share one policy version string.
- The degraded list has no expiry.
- The client simulator follows documentation and was never run against live Amp or Copilot. It matches package name and registry type, not version.
- The slice vets the tools a submitter declares, not what the running server exposes.
- From the manual smoke test: the 422 message repeats the received value, scanner findings are labelled "offending text" but show the scanner's summary, and a refused review attempt is not written to the audit trail.
