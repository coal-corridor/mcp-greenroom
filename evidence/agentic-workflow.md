# Agentic workflow: MCP Greenroom

Sections 1 and 2 were written before the timed build and are completed here. Sections 3 to 7 were rewritten after it, from `evidence/session-log.md`, the handoff notes and review reports in `handoff/`, and the git history. All times are local (Sydney), 17 Nov 2026. Nothing in this file may describe a result that was not produced. My answers to the questions left open by the first draft (sections 1, 2 and 6, and the timeline) were drafted with the steering chat from the record of the build and checked by me.

## 1. Tools

| Tool | Used for |
| --- | --- |
| Claude Code (CLI) | Primary implementation tool: all code, tests, scripts and the evidence pack. Four sessions, lead, vetting, registry and edge, each on Opus 5.5 in its own git worktree. Effort: lead high, vetting high, registry medium, edge `TODO(user)`: which effort did the edge session use? Permission mode: plan mode until each plan was approved, then accept edits in the lead session (13:48), auto mode from about 14:19. The area sessions ran in auto mode from plan approval |
| Claude (chat) | Preparation: study notes, idea selection, intent, spec, README overview, roadmap, this skeleton. During the build: one session used throughout for prompt wording, permission prompts and review triage |
| GitHub Spec Kit, driven from Claude Code | Preparation only: one idea assessment pass (intake, research, problem, concept) |
| Anthropic API, through the slice's live provider | The two classifier recording runs only, behind `make record` (an ask rule). Run 1 on `claude-opus-5-5` (`827782a`), run 2 on `claude-haiku-5-5` (`66567b5`), which is the one in the tree. Each sent 61,891 input tokens; output was 2,873 and 6,432 tokens (`handoff/vetting.md`) |

The harness is committed in the repo, so the panel can read what steered the agent:

- `CLAUDE.md`: commands, conventions, pitfalls, holding only what cannot be read from the repo. Amended once during the build, in its own commit, to name the config module and the logger (`68cf5a3`). `AGENTS.md` is a pointer to it, for agents that look for that name.
- `.claude/settings.json`: an allow list of known-safe commands, deny rules for secrets, for history rewrites and for hand edits to the classifier recordings, a `Stop` hook that runs the check script, a format hook, and a `SessionStart` hook that prints the session brief.
- `.claude/agents/`: one read-only reviewer subagent.
- `.claude/skills/`: seven project skills. Claude starts `verify-change`, `tdd-behaviour`, `write-evidence` and `handoff`. I start `/review-area`, `/open-area-pr` and `/record-classifier`, because they review, push or call a model.

The plan also named the built-in `/code-review` and `/security-review` for integration, and the `claude-api` skill for the live provider. The user ran `/security-review` on `integration` at 16:05; `/code-review` was not run, cut for time by the user (`handoff/integration-review.md`). There is no sign that the `claude-api` skill was used: neither `handoff/vetting.md` nor any commit message mentions it, and the live provider speaks the Messages API over httpx with no SDK, as `vetting.md` asks. `/status` was not captured during the build, so only this can be checked: the user settings file (`~/.claude/settings.json`) sets `syncClaudeAiSkills: false`, `syncClaudeAiPlugins: false` and `disableClaudeAiConnectors: true`, and no plugin was installed. The only skills beside Claude Code's built-in ones were the seven in this repo.

## 2. Prepared in advance

| Artefact | Made with | In this repo |
| --- | --- | --- |
| Study notes on agentic engineering practice, eight sources, and a synthesis of takeaways | Claude chat and Claude Code | No |
| Gap analysis of one agent platform's public documentation, a shortlist of three ideas, the choice of this one | Claude chat | No |
| Idea assessment: intake, research, problem, concept | Claude Code with Spec Kit | No |
| An earlier design draft with API contracts, decision rules and sample outcomes | Claude chat | No. The spec replaces it and inherits its decision order and samples |
| `intent.md`, the spec (a parent and five child specs) and its notes file | Claude chat | Yes |
| README overview, `ROADMAP.md`, `references.md`, this skeleton | Claude chat | Yes |
| The seven project skills and the reviewer agent definition | Claude chat | Yes, under `.claude/` |
| `AGENTS.md`, `CLAUDE.md`, `.claude/settings.json` with three hook scripts, the briefs and the headings of the remaining evidence files | Claude chat | Yes |
| The planned prompt for each phase and the steering rules for the user | Claude chat | Not in the tree. The prompts actually sent are in section 4 |
| `TODO(user)`: `pyproject.toml` (`86697af`, 13:58), the check script (`0be6efe`, 14:00) and the CI workflow (`b07f740`, 14:08) were committed inside the timebox. Were any of them copied from a template prepared in advance? If not, delete this row | | |
| Build environment: WSL 2 with Ubuntu 24.04, toolchain checked by a probe script, a trimmed Claude Code profile | By hand and with Claude Code | No |

No practice pass was run. The tree at `0b4ecd9`, the head of `main` when the build started at 13:38, holds no file under `src/`, `tests/`, `sample-data/`, `evals/` or `scripts/`. The first package code was committed at 13:58 (`86697af`), the sample servers at 14:22 (`0eea3c2`) and the first classifier recordings at 15:11 (`827782a`). The full-history secret scan finds no leak in 224 commits (`verify.md`). There were no earlier attempts at building. The API key for the recording run was created and tested with one call before 13:38, and was never committed.

## 3. How the work was decomposed

What happened. Commits per scope at `f117754`: setup 14, contracts 16, registry 34, edge 65, vetting 98, integration 15, plus 5 merge commits.

1. **Frame**, brief 00, 13:38 to 14:08, lead. Lockfile and empty package, a check script with its test stage still failing, the network guard and structure tests, the CI workflow. Pull request 1 opened at 14:10, run 44008340480 green.
2. **Contracts**, brief 10, 14:08 to 14:27, lead. Pinned upstream documents (`f343f5d`), shared models, config, logging, fingerprint, seams, five samples, fakes, each red then green. Frozen at `3e8f6e6`. Pull request 1 merged at 14:30 (`2ca2349`).
3. **Build**, 14:35 to 15:45. Three area sessions in their own worktrees. They started together, not staggered as planned, because the build window was about half the planned one. Each worked one behaviour at a time as a red and a green commit, ran the reviewer, took the user's decision on each finding, and opened its pull request. Merged in order of completion: registry (#2, 15:12), edge (#3, 15:31), vetting (#4, 15:44), not the planned vetting, registry, edge.
4. **Integrate**, brief 90, from 15:46, lead on branch `integration`. The real pipeline built once at startup and the fakes replaced in the end-to-end test (`9440b6f`, `50caca5`), `get_store` typed (`b328724`), the scanner pinned (`3414367`), a policy change without a new policy version stops startup (`d4516d1`), demo output saved, and a break test on two fresh clones with two fixes (`295941b`, `94dc6a4`). Then the integration reviews: `/review-area` and `/security-review` on `f117754`, recorded with the user's decisions at 16:14 (`868faee`), three review fixes test first and a scanner lock (16:14 to 16:17). Pull request 5 merged at 16:23 (`2b6ee66`), run 44023747644 green on all five jobs.
5. **Evidence**, brief 95, on branch `evidence`, cut from `integration`, while the lead session finished the integration reviews. One commit per file, the first at 16:13.
6. **Clean clone.** Two fresh clones in this pass, before and after the README commit. Both green (`verify.md`).

Decided in advance, and what changed:

- **Topology.** Parallel sessions in git worktrees, as planned, but all three areas started at once instead of staggered. The reviewer subagent ran once per area.
- **Context handover.** As planned: a brief and a handoff note per session, the note printed into the next session by the `SessionStart` hook. 34 commits touch `handoff/`. The lead note lived on a local branch, `lead/handoff`, and was merged into `integration` (`7246f7b`). The three review reports are committed beside the notes.
- **Classifier recordings.** Planned as one run; there were two. The Opus run refused 17 of 47 tools, all hostile; each refusal went to human review and the gate failed on the `poisoned-notes` sample. The Haiku run had no refusals. The gate then failed only on the reasons given for `ambiguous-exporter`, and passed once the user had that sample checked on outcome and tier (`d609a19`). The Opus run is kept in history.

## 4. Steering

Standing instructions live in `CLAUDE.md` and in the spec ("stop and ask" at the edges of scope). One standing instruction was added during the build, at 14:41: work the brief without checking in after each behaviour, and commit each green route.

`TODO(user)`: two or three prompts exactly as sent, each with the commit it led to. The prompt for this evidence pass is below, as sent; keep it or replace it.

| Prompt as sent | Step | Resulting commit |
| --- | --- | --- |
| "Read briefs/95-evidence.md and follow it with the write-evidence skill. You are on branch evidence, cut from integration, while the lead session finishes the integration reviews. Run uv sync first. [...] Order: verify.md, operate.md, design.md, README.md (the Setup section first, it is still a placeholder), agentic-workflow.md, then the factual parts of decisions.md. [...] Where only I know the answer, leave TODO(user) with the question and list those at the end. Do not guess, and do not write trade-offs in my voice. One commit per file. Do not check in between files." | Evidence | `5bfcdc8` to this file's commit |
| `TODO(user)` | | |

## 5. Where I intervened

Drafted from `evidence/session-log.md`. `TODO(user)`: check each row, and add any `Esc`, rewind, `/clear` or restart, none of which is in the log.

| Time | What the agent did or proposed | What I changed, and why | Trace |
| --- | --- | --- | --- |
| 13:44 | Lead plan said the repo had no commits | Rejected it: three commits on `main`, no baseline commit. Also: leave the scanner out if it does not install cleanly | Revised plan, head `0b4ecd9` |
| 13:54 | `uv audit` found two `litellm` advisories | Kept the scanner and waived both IDs: both are in the proxy, which never runs | `fabf418`, `decisions.md` |
| 14:05 | Researched the gitleaks action | Stopped it after three lookups: setup was at 27 minutes against 10. Asked for the simplest full-history scan | `b07f740`, `a6b4466` |
| 14:14 | Contracts proposal | Approved with two changes: the env names of `.env.example`, recordings in `evals/recordings/` | `f343f5d` |
| 14:19 | Approval prompts were costing most of the lost time | Switched to auto mode. Deny and ask rules still hold | |
| 14:24 | Found that recording every sample would break the Abstain criterion | Spec and skill changed to leave `unrecorded-reporter` unrecorded | `3e8f6e6` |
| 14:38 | Scanner import makes LiteLLM try the network | Approved setting `LITELLM_LOCAL_MODEL_COST_MAP` in the frozen `config.py`; adapter moved last, with a cut option | `4dd0c9a` |
| 14:41 | `get_identity` gained a header parameter | Ruled not a change to the frozen seam. Told the sessions to continue without check-ins | `15b5c92` |
| 14:44 | Allowed package sources | A strict list as a constant in the policy code; a setting is roadmap work | `48df227` |
| 14:50 | `cli.py` near the 350-line limit | Approved a second file, `cli_output.py`; structure test unchanged | `6cfda8c` |
| 15:09 | `.dockerignore` outside the edge area | Approved: keeps `.env` and `.git` out of the build context | `9ff3a91` |
| 15:16 | Gate failed on the reasons of `ambiguous-exporter` | Check outcome and tier only for that sample. No threshold moved | `d609a19` |
| 15:39 | Secret scan red on 47 replay keys | Approved a `.gitleaks.toml` allowlist that needs both the recordings path and a 64-hex value | `eedd2ca` |
| 15:03 to 15:28 | Three review reports, 37 findings | A decision on every finding | `handoff/*-review.md` |
| 16:05 to 16:14 | Integration review, 6 findings and one point not verified | A decision on every finding, a lock on the scanner, `/code-review` cut for time | `868faee` |

## 6. How output was reviewed

What happened.

- **Enforced.** The `Stop` hook ran lint, types and tests at the end of each agent turn; a second stop in a row passes with a warning. CI ran five jobs on every pull request and push to `main`. Deny and ask rules held throughout. Auto mode's safety check blocked one command at 15:39, which wrote a config file and downloaded the gitleaks binary in one step. Not enforced: no check is marked required, because the repository is private.
- **Reported, not enforced.** The dependency audit: no finding after the two waivers.
- **By me.** I merged all five pull requests by hand, on green, and decided every review finding. I read most diffs and commit messages line by line during the build. The merges relied on green checks, the independent reviewer's reports and my decision on each finding.
- **Independent.** The reviewer subagent, once per area and once on `integration`, started with `/review-area`, given the parent spec, the child spec and the diff. Areas: 37 findings, 6 High, all High fixed. Integration: 6 findings, none High, and one point it could not verify (scanner thread safety). The built-in `/security-review` over `main...integration` reported no vulnerabilities; no finding reached its 80% confidence bar. `/code-review` was not run. Counts and decisions are in `verify.md`.
- **Caught late.** A command chain that hid the exit code let a failing check be committed in three sessions: lead (`9b3d50f`, fixed in `ffa1567`), vetting (two tier commits, fixed in `22da938`) and edge (`3c735e5`, fixed in `f6e0bd5`). The next check caught each one after the commit, not before.
- **Caught by tests and CI.** A unit test caught a provider answering for the wrong tool, which led to approval (`9e460f6`). CI caught a difference the local run missed: Typer forces colour in `--help` under `GITHUB_ACTIONS` (`500774a`).
- **By hand.** The lead session ran the break test from two fresh clones, with a script that prints each command, its output and exit code (`evidence/raw/break-test.txt`). Run 1 at `a32cf5f` found no stack trace and two unclear messages: a missing file and broken JSON gave the same message naming only the exception class, and a list with the store down and no last-good copy said "nothing can be submitted or decided". Both were fixed test first (`47f113a` red, `295941b` and `94dc6a4` green), and run 2 at `94dc6a4` confirmed them. One weak message was left as is: a JSON array as the body. This pass drove the running service with `curl` (`operate.md`).
- **Documents.** Every evidence file in this pass is written from commands run in it, including two fresh clones.

| Finding | Accepted or rejected | Why | Commit |
| --- | --- | --- | --- |
| Registry 1, High: unhandled exceptions logged raw by uvicorn, outside `log_event` | Accepted, fixed | | `809b877` |
| Registry 2, High: the refusal test could not fail | Accepted, fixed | | `755ecf2` |
| Edge 1, High: any import error could skip the end-to-end test | Accepted, fixed | | `b5c71b4` |
| Vetting 1 to 3, High: remotes, npm specifier forms and registry-override arguments get around the source allowlist | Accepted, fixed | | `760577d`, `cde934a`, `65a6f27` |
| Edge 4: `uvx --with` let a second package past the client check | Accepted, fixed | | `39fa3d1` |
| Vetting 4: thresholds can change without the policy version | Deferred to integration | `config.py` is frozen; the lead decides | `d4516d1` in part; the rest in `ROADMAP.md` |
| Edge 3: client check ignores the version | Accepted as is | Follows the spec, which mirrors the client's documented check | `ROADMAP.md` |
| Edge 2 and vetting 12: files edited outside the area | Accepted as is | Approved in the session | |
| Integration 1: tests in `api/`, `e2e/` and `failure/` read the shell's settings, the key included | Accepted, fixed | | `485c8b3`, `778aeb2` |
| Integration 3: a pipeline that cannot be built gives a traceback and loses degrade mode | Accepted, fixed in its small version | Serving the last-good list without a pipeline went to the roadmap | `cd404d3`, `32004b2` |
| Integration 4: main path test did not check "by policy" | Accepted, fixed | | `fb0260c` |
| Integration, not verified: scanner shared across threads | Lock added; listed as not verified | | `6e5c5dd`, `6332a84` |
| Integration 2: two policies can share one version | Accepted as a known gap | Already on the roadmap | |
| Integration 5: `get_store` returns the concrete store | Accepted; docstrings corrected | | `d416b30` |
| Integration 6: `read_submission` loosely typed, branches untested | Deferred | Roadmap | `2399081` |
| The other 26 area findings | See the review files | Each has a recorded decision | `handoff/*-review.md` |

## 7. Timeline

From the time ledger in `session-log.md`. One sitting. No phase was replayed.

| Phase | Budget | Start | End | Notes |
| --- | --- | --- | --- | --- |
| Frame and contracts | 0:00 to 0:20 | 13:38 | 14:27 | 49 minutes: setup 30, contracts 19 |
| Merge of pull request 1, worktrees, area plans | | 14:27 | 14:35 | 8 minutes |
| Build | 0:20 to 1:50 | 14:35 | 15:45 | 70 minutes, three sessions in parallel |
| Integrate and review | 1:50 to 2:25 | 15:46 | 16:23 | Break test fixes by 16:00 (`f117754`), review fixes by 16:18 (`b6a8acc`), pull request 5 merged at 16:23. Overlapped with the evidence pass |
| Evidence | 2:25 to 2:55 | 16:05 | Open until its pull request merges | A second lead session, in auto mode. First evidence commit at 16:13 |
| Clean clone | 2:55 to 3:00 | | | Fresh clones at 16:09 and after 16:17, and one on the merged state (`verify.md`) |

Building time: 127 minutes to 15:45, and 164 to 16:23 when integration ended. Integration and evidence overlap from 16:05 to 16:23, counted once. The evidence pass after 16:23 adds to this until its pull request merges.
