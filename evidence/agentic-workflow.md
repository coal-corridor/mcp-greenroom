# Agentic workflow: MCP Greenroom

Status: skeleton, written before the timed build. Sections 1 and 2 record the preparation. Sections 3 to 7 hold the plan. After the build they are rewritten from what actually happened, and every line marked `TODO(build)` is replaced or deleted. Nothing in this file may describe a result that was not produced.

## 1. Tools

| Tool | Used for |
| --- | --- |
| Claude Code (CLI) | Primary implementation tool: all code, tests, scripts and the evidence pack. `TODO(build)`: model, effort and permission mode, from `/status` |
| Claude (chat) | Preparation only: study notes, idea selection, intent, spec, README overview, roadmap, this skeleton |
| GitHub Spec Kit, driven from Claude Code | Preparation only: one idea assessment pass (intake, research, problem, concept) |

The harness is committed in the repo, so the panel can read what steered the agent:

- `CLAUDE.md`: commands, conventions, pitfalls, holding only what cannot be read from the repo. Amended at each correction, in its own commit. `AGENTS.md` is a pointer to it, for agents that look for that name.
- `.claude/settings.json`: an allow list of known-safe commands, deny rules for secrets, for history rewrites and for hand edits to the classifier recordings, a `Stop` hook that runs the check script, a format hook, and a `SessionStart` hook that prints the session brief.
- `.claude/agents/`: one read-only reviewer subagent.
- `.claude/skills/`: seven project skills. Claude starts `verify-change`, `tdd-behaviour`, `write-evidence` and `handoff`. I start `/review-area`, `/open-area-pr` and `/record-classifier`, because they review, push or call a model.

Beyond these, the plan uses the built-in `/code-review` and `/security-review` at integration, and the `claude-api` skill for the live provider. No other plugin is planned. `TODO(build)`: list any skill or plugin that was enabled beyond these, and confirm the profile was otherwise clean (plugin list and the "Setting sources" line from `/status`).

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
| `TODO(build)`: if the templates were copied (check script, CI workflow, `pyproject.toml`), list them here. If the agents wrote them inside the timebox, delete this row | | |
| Build environment: WSL 2 with Ubuntu 24.04, toolchain checked by a probe script, a trimmed Claude Code profile | By hand and with Claude Code | No |

`TODO(build)`: state whether a practice pass was run, in which repository, and what was carried over from it. State plainly whether any implementation code, test, sample or classifier recording existed before the timebox started. Confirm that the API key for the recording run was set in the shell before the timebox and was never committed.

## 3. How the work was decomposed

Plan. Replace with what happened.

1. **Frame.** Create the public repo. First commits: the prepared documents, `CLAUDE.md`, settings and hooks, a check script that fails, the upstream OpenAPI document and schema pinned with URL and date, and the CI workflow with its required checks. From then on every pull request is gated. The workflow only calls the check script, so it does not wait for feature code and can be handed to a parallel session.
2. **Contracts.** Shared models, configuration, sample submissions with expected outcomes, and the seams between parts. I freeze these before any parallel work starts.
3. **Build.** Test first, one behaviour per commit. Three areas with separate folders: registry (API, store, last-good copy, audit), vetting (rules, classifier providers, evaluation), edge (CLI, client simulator, scripts, container files). Each area lands through its own pull request, with one more for setup and one for integration.
4. **Integrate.** Merge the pull requests with merge commits once their checks are green, run the fresh-context review, run the demo.
5. **Evidence.** README and evidence pack, written from real output.
6. **Clean clone.** Check script green in a fresh directory.

Decided in advance:

- **Topology.** Parallel Claude Code sessions in git worktrees, staggered. Each session loads the parent spec and the one child spec for its area. Vetting and registry start once the contracts are frozen, while the lead session sets up CI and drafts `design.md` and `decisions.md`. The edge session starts third. Subagents are used only for bounded jobs whose result is a report, such as the fresh-context review.
- **Context handover.** State crosses sessions as files, not as conversation: the parent spec and one child spec, a brief per session, and a handoff note per session in `handoff/` that holds the approved plan, what is done with its tests, the open items and the next step. The note is written at each phase close and printed into the next session by a hook, also after `/clear` and after a compaction. Subagents start cold: the reviewer gets the spec and the diff, never the builder's reasoning. Reviewer reports are committed beside the notes.
- **Classifier recordings.** One run of the live provider against the Anthropic API during the build. The key is held in the shell environment and is never in the repo.

## 4. Steering

Standing instructions live in `CLAUDE.md` and in the spec ("stop and ask" at the edges of scope). Prompts I plan to reuse:

- Opening a session: "Review changes made today, then run `./scripts/verify.sh`."
- Ending each feature prompt: "Use red/green TDD."
- Near the end: "Run a dev server and explore the API using `curl`, including the rejection path. Record each command and its output."

`TODO(build)`: two or three prompts exactly as sent, each with the commit it led to.

| Prompt as sent | Step | Resulting commit |
| --- | --- | --- |
| `TODO(build)` | | |

## 5. Where I intervened

Sources: commits that amend `CLAUDE.md`, rejected plans, scope cuts, restarted sessions.

| Time | What the agent did or proposed | What I changed, and why | Trace |
| --- | --- | --- | --- |
| `TODO(build)` | | | |

## 6. How output was reviewed

Plan. Replace with what happened.

- **Enforced.** The check script (lint, types, tests, evaluation gate) through the `Stop` hook. The pull request checks, required before any merge to `main`: the same stages as parallel jobs, plus a secret scan. Deny rules. None of these depend on the agent choosing to comply.
- **Reported, not enforced.** The dependency audit runs on every pull request and does not block, because its result depends on an external advisory list. I read its result before each merge.
- **By me.** I read every diff and every commit message before it lands on `main`, and I am the only one who merges.
- **Independent.** A read-only reviewer subagent with a fresh context, given only the parent spec, the child spec of the area under review and the diff. Its checklist: acceptance criteria and invariants hold, no path approves when a rule or the classifier has stopped a case, separation of duties is enforced on the server, no secrets, no network in tests, an audit record for every decision, tests assert behaviour, README commands run.
- **By hand.** The agent drives the running service, including the failure paths. The real commands and output are kept, not a summary.
- **Documents.** Every evidence file is written from real output. No recording, result or number is written by hand.

`TODO(build)`: reviewer findings and my decision on each.

| Finding | Accepted or rejected | Why | Commit |
| --- | --- | --- | --- |
| `TODO(build)` | | | |

## 7. Timeline

Provisional budget. Start and stop times are written at each phase boundary during the build. The three hours are spread over more than one sitting, as the exercise allows. Breaks are not building time. A replayed phase counts in full. `TODO(build)`: total building time across all attempts, from the time ledger in `session-log.md`, and each replay with its reason.

| Phase | Budget | Start | End | Notes |
| --- | --- | --- | --- | --- |
| Frame and contracts | 0:00 to 0:20 | `TODO(build)` | | |
| Build | 0:20 to 1:50 | | | |
| Integrate and review | 1:50 to 2:25 | | | |
| Evidence | 2:25 to 2:55 | | | |
| Clean clone | 2:55 to 3:00 | | | |
