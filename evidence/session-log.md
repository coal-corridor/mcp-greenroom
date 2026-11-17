# Session log

Notes on the build, one line per event. This file feeds the interventions and the timeline in `agentic-workflow.md`.

Entries up to 15:50 were written up at 15:50 from the timestamped messages of the chat used to steer the build, so times are accurate to a few minutes. Commit hashes are as the sessions reported them, and were checked against `git log` and `gh` on 17 Nov. Entries from 15:50 on were added afterwards from `git log`, `gh` and the handoff notes, so their times are commit or run times. All times are local (Sydney), 17 Nov 2026.

## Time ledger

One row per phase of the one sitting so far. Building time counts whether the attempt was kept or replayed. Breaks do not count.

| Phase | Attempt | Start | Stop | Minutes | Kept or replayed | Running total |
| --- | --- | --- | --- | --- | --- | --- |
| Setup (brief 00) | 1 | 13:38 | 14:08 | 30 | Kept | 30 |
| Contracts (brief 10) | 1 | 14:08 | 14:27 | 19 | Kept | 49 |
| Merge of pull request 1, worktrees, area plans | 1 | 14:27 | 14:35 | 8 | Kept | 57 |
| Areas in parallel (vetting, registry, edge) | 1 | 14:35 | 15:45 | 70 | Kept | 127 |
| Integration (brief 90) | 1 | 15:46 | 16:23 | 37 | Kept | 164 |
| Evidence (brief 95) | 1 | 16:05 | Open until the evidence pull request merges | | Kept | |

Integration and evidence overlap from 16:05 to 16:23. Count those 18 minutes once.

## Events

| Time | Session | What happened | Why | Trace (commit, file) |
| --- | --- | --- | --- | --- |
| 13:38 | lead | Build started. Opus 5.5, effort high, plan mode. First prompt sent with a note that the repo is private. | Required checks cannot be switched on for a private repo on this plan. The user merges on green by hand. | `briefs/00-setup.md` |
| 13:38 | user | A Claude chat session is used through the build for prompt wording, permission prompts and review triage. | One person steering up to four sessions. | `agentic-workflow.md`, section 1 |
| 13:44 | lead | Plan rejected once. It said the repo had no commits. Corrected: three commits on `main`, no baseline commit. Second correction: leave the scanner package out if it does not install cleanly. | A false premise in the plan. | Revised plan, head `0b4ecd9` |
| 13:48 | lead | Plan approved. Mode: accept edits. | Auto mode was left out of the plan. | |
| 13:54 | lead | `uv audit` found two advisories in `litellm 1.93.2`, pinned by `cisco-ai-mcp-scanner` 4.8.7. The user chose to keep the scanner and waive both IDs. | Both are in the LiteLLM proxy, which is never started. | `fabf418`, `evidence/decisions.md` |
| 14:05 | lead | The user stopped the agent's research into the gitleaks action after three read-only lookups and asked for the simplest setup that scans the full history. Result: a pinned gitleaks 8.30.1 binary with a sha256 check. | Setup was at 27 minutes against a budget of 10. | `b07f740`, `a6b4466` |
| 14:08 | lead | Brief 00 done: check script green, 17 tests, `eval` skipped. Slip: `9b3d50f` was committed with a lint failure because the command read the exit code of `tail`. Fixed in the next commit. | Hidden exit code in a command chain. | `9b3d50f`, `ffa1567` |
| 14:10 | lead | Pull request 1 opened. All five jobs green. | | Run 44008340480 |
| 14:14 | lead | Contracts proposal approved with two changes: keep the env names of `.env.example`, default the recordings folder to `evals/recordings/`. | Consistency with what was already written down. | `f343f5d` (pinned upstream documents) |
| 14:19 | lead | Switched to auto mode. Area sessions use it from plan approval. | Most of the lost time went on approval prompts. Deny and ask rules still hold. | `evidence/decisions.md` (to add) |
| 14:24 | lead | The agent found that recording every sample would break the Abstain criterion. The user had the skill and the spec changed to leave out `unrecorded-reporter`. | Contradiction between the skill, the spec and a criterion. | `3e8f6e6` |
| 14:27 | lead | Contracts frozen. `CLAUDE.md` now names the config module and the logger. | Milestone 1. | `68cf5a3`, run 44010204313 |
| 14:30 | user | Pull request 1 merged. Three worktrees created. | | `2ca2349` |
| 14:35 | vetting | Session started. Opus 5.5, effort high. First move: scanner fit test. | The test was moved from preparation into the build. | `handoff/vetting.md` |
| 14:37 | registry | Session started. Opus 5.5, effort medium. | | `handoff/registry.md` |
| 14:38 | vetting | Fit test: the scanner fits, the benign sample is clean, `poisoned-notes` gets two HIGH findings. Importing it makes LiteLLM try the network unless `LITELLM_LOCAL_MODEL_COST_MAP` is set. The user approved setting it in the frozen `config.py` and put the adapter last, with a cut option. | Keeps one module in charge of the environment. Never-cut items come first. | `4dd0c9a` |
| 14:40 | edge | Session started together with the other two, not third as planned. It began with the parts that do not need the registry's routes. | The build window was about half the planned one. | `handoff/edge.md` |
| 14:41 | registry | `get_identity` gained a header parameter. Ruled not a change to the frozen seam. Sessions told to continue without checking in after each behaviour. | Name, return type and override point are unchanged. | `15b5c92` |
| 14:44 | vetting | Allowed sources: the strict list (npm and PyPI public registries) stays as a constant in the policy code. | Fail closed. A setting is roadmap work. | `vetting/policy.py` |
| 14:50 | edge | `cli.py` was near the 350-line limit of the structure test. The user approved a second file, `cli_output.py`. | Keep the structure test as it is. | `briefs/area-edge.md` |
| 15:00 | vetting | A unit test caught a real bug: a provider that answered for the wrong tool led to approval. Fixed. | | `9e460f6` |
| 15:03 | registry | Independent review: 13 findings, 2 High (unhandled exceptions logged raw by uvicorn, one test that could not fail). Seven fixed, the rest deferred with a decision each. | | `handoff/registry-review.md`, `d102d2f` |
| 15:07 | vetting | Recording run 1, `claude-opus-5-5`: 17 of 47 tools refused (all 16 malicious cases and the hostile tool of `poisoned-notes`). Every refusal went to human review, none was approved. Kept in history. | The classifier declined hostile input and the pipeline failed closed. | `827782a` |
| 15:09 | edge | `.dockerignore` added outside the area, approved by the user. | Keep `.env` and `.git` out of the build context. | `9ff3a91` |
| 15:14 | edge | Independent review: 11 findings, 1 High (end-to-end test could be skipped by any import error). One Medium was a bypass: `uvx --with` allowed a second package. Five fixed, the rest deferred with a decision each. | | `handoff/edge-review.md`, `e146b68` |
| 15:16 | vetting | Recording run 2, `claude-haiku-5-5`: no refusals, all 16 malicious cases rejected, 24% of cases in review, `poisoned-notes` rejected at 0.97. The gate failed on a reason check for `ambiguous-exporter`. The user chose to check outcome and tier only for that sample. | The samples table fixes outcomes, not reasons. No threshold was moved. | `66567b5`, `d609a19` |
| 15:19 | vetting | Scanner adapter green inside the cap. Nothing cut. | | `scanner/yara.py` |
| 15:24 | user | Pull request 2 (registry) merged on green. | | Pull request 2 |
| 15:25 | edge | `verify (test)` red on GitHub, green locally. Cause: Typer forces colour in `--help` when `GITHUB_ACTIONS` is set. The tests now strip colour codes, with the same assertions. | Difference between the local and the CI environment. | `500774a` |
| 15:28 | vetting | Independent review: 13 findings, 3 High, all ways around the source allowlist (remotes, npm specifier forms, registry override arguments). Ten fixed, two deferred, two accepted. | | `handoff/vetting-review.md`, `0dc41f8` |
| 15:31 | user | Pull request 3 (edge) merged on green. | | Pull request 3 |
| 15:39 | vetting | Secret scan red on pull request 4: 47 findings on the replay key of the recordings in `827782a`. False positive: each value is a SHA-256 equal to the file name. The user approved a `.gitleaks.toml` allowlist that needs both the path and a 64-hex value. | The scan covers the full history and history is not rewritten. | `eedd2ca`, `cc5760a` |
| 15:39 | vetting | The auto mode safety check blocked a command that wrote the config file and downloaded the gitleaks binary in one step. The agent wrote the file alone and skipped the local test. | CI over the full history confirmed the allowlist. | Pull request 4 |
| 15:45 | user | Pull request 4 (vetting) merged on green. Merge order was registry, edge, vetting, not the planned vetting, registry, edge. | Order of completion. | Pull request 4 |
| 15:46 | lead | Integration started in auto mode on branch `integration`. | | `briefs/90-integrate.md` |
| 15:50 | lead | Real pipeline built once at startup and the end-to-end test run without fakes. `get_store` returns `SqlStore`. Scanner pinned at `==4.8.7`. | Wiring the areas together, and two items deferred from the registry review. | `9440b6f`, `50caca5`, `b328724`, `3414367` |
| 15:52 | lead | Deferred review items listed in `ROADMAP.md`. Real demo and check output saved. | | `593994f`, `394e7be` |
| 15:55 | lead | A policy change without a new policy version stops startup. The user approved the change to the frozen `config.py`. The full hash-stamped version went to the roadmap. | Vetting review finding 4, deferred to integration. | `7dbe638`, `d4516d1`, `a32cf5f` |
| 15:56 | lead | Break test, run 1, from a fresh clone at `a32cf5f`: no stack trace, two unclear messages. | Brief 90, step 6. | `evidence/raw/break-test.txt` |
| 15:59 | lead | Both messages fixed test first. Run 2 from a new fresh clone at `94dc6a4` confirmed them. One weak message left as is. | | `47f113a`, `295941b`, `94dc6a4`, `50fca42`, `f117754` |
| 16:05 | user | `/security-review` over `main...integration`: no vulnerabilities reported. `/review-area` on `integration`: six findings and one point not verified. `/code-review` cut for time. | Brief 90, step 4. | `handoff/integration-review.md` |
| 16:05 | lead | Evidence pass started in a second session on branch `evidence`, cut from `integration`, in auto mode. | The integration reviews were still running. | `briefs/95-evidence.md` |
| 16:13 | lead (evidence) | Fresh clone at `f117754` green. Six evidence files written, one commit each, with `TODO(user)` where only the user knows the answer. | | `5bfcdc8` to `e06a453` |
| 16:14 | lead | Integration review decisions recorded. Fixed test first: every test folder clears the shell's settings, the main path test checks "by policy", a pipeline that cannot be built stops startup clearly. A lock on the shared scanner. | The user's decision on each finding. | `868faee`, `485c8b3`, `778aeb2`, `fb0260c`, `cd404d3`, `32004b2`, `6e5c5dd`, `6332a84` |
| 16:23 | user | Pull request 5 (integration) merged. Run 44023747644 on `2b6ee66` green on all five jobs. | | `2b6ee66` |
| 16:24 | lead (evidence) | `main` merged into `evidence`. Check script (436 passed) and demo re-run, `verify.md` and `agentic-workflow.md` updated with the integration review. | | `38c46d7`, `e0c7a10`, `19ac383` |
| 16:35 | user | Answers to the `TODO(user)` questions, drafted with the steering chat from the record of the build and checked by the user. | | `evidence/agentic-workflow.md`, `evidence/decisions.md` |
| 16:40 | lead (evidence) | The Stop hook blocked the turn: `test_untrusted_text_is_printed_inert` failed in the hook's 64-column shell, because the findings table wrapped inert text across two lines. CI, at a wider width, did not catch it. The user approved one test-only fix outside the brief: the CLI tests pin `COLUMNS=120`. | A test that depended on the width of the shell. | `a3ee25f` |

## Repeated mistake

Committing with a failing check because a command chain hid the exit code happened in three sessions: lead (`9b3d50f`), vetting (two commits, one fixed in `22da938`) and edge (`3c735e5`, fixed in `f6e0bd5`).
