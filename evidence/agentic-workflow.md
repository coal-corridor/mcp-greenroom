# Agentic workflow: MCP Greenroom

## Agentic tools

### 1. Claude Code (CLI) - Primary implementation tool for code, tests, scripts and the evidence pack.

Four sessions, lead, vetting, registry and edge, each on Opus 5.5 in its own git worktree.

Effort by session
- lead: high
- vetting: high
- registry: medium
- edge: medium.

Permission mode
- Plan mode until each plan was approved, 
- Accept edits in the lead session
- Area sessions ran in auto mode post plan approval

### 2. Claude (chat) - Preparation: study notes, specs, docs, roadmap, initial agent harness skeleton

### 3. Anthropic API, through the slice's live provider
The two classifier recording runs, behind `make record` (an ask rule). 
- Run 1 on `claude-opus-5-5` (`827782a`) 
- Run 2 on `claude-haiku-5-5` (`66567b5`), went into the tree. 

Each sent 61,891 input tokens; output was 2,873 and 6,432 tokens (`handoff/vetting.md`) |

### Agentic harness

- `CLAUDE.md`: commands, conventions, pitfalls, holding only what cannot be read from the repo.
- `AGENTS.md` is a pointer to it, for agents that look for that name.
- `.claude/settings.json`: a command allow list, deny rules
- `.claude/agents/`: a reviewer subagent.
- `.claude/skills/`: project skills (`verify-change`, `tdd-behaviour`, `write-evidence`, `handoff`, `/review-area`, `/open-area-pr` and `/record-classifier`)

**Hooks**:
- A PostToolUse hook for Python formatting (`format-on-write.sh`)
- A Stop hook for tests after each turn (`stop-verify.sh`)
- A SessionStart hook for context management, starts session with a short brief (`session-brief.sh`)

**The user settings** (`~/.claude/settings.json`) 
```json
{
  "syncClaudeAiSkills": false,
  "syncClaudeAiPlugins": false,
  "model": "opus",
  "disableClaudeAiConnectors": true,
  "modelSettings": {
    "claude-opus-5-5": {
      "effortLevel": "high"
    }
  }
}
```
## Decomposition
### Session topology (in order of execution)
- Planning session (lead)
- Three parallel sessions in git worktrees for building (vetting, registry, edge), the reviewer subagent ran once per area
- Two parallel sessions in git worktrees for integration workflows (integration) and evidence logging (evidence)

### Context handover.
A brief and a handoff note per session, the note printed into the next session by the `SessionStart` hook. 

### Classifier recordings.
- Planned as one run; two were executed.
- The Opus run refused 17 of 47 tools, all hostile; each refusal went to human review and the gate failed on the `poisoned-notes` sample. 
- The Haiku run had no refusals. 
- The Opus run is kept in history.

## Steering

| Sample prompts as sent | Step | Resulting commit |
| --- | --- | --- |
| "Read `docs/specs/mcp-greenroom.md`, `docs/specs/delivery.md` and `briefs/00-setup.md`. Tell me in ten lines or fewer what you will do, and list anything that looks wrong or contradictory. Do not write code until I say go. Note: the GitHub repo is private for now, so required checks cannot be switched on yet; I merge only on green by hand and will switch them on when the repo goes public, so do not treat that as a blocker." | 13:38, lead, opening | The setup commits, `86697af` onward |
| "Two corrections, the rest is approved. (1) `main` already has three commits, all pushed: confirm with `git log --oneline -5` and `git status`. Skip the baseline commit and create branch `setup` from `main`. If `git log` shows no commits, stop and tell me. (2) If `cisco-ai-mcp-scanner` does not resolve or install cleanly, leave it out of `pyproject.toml` and tell me. Do not debug it in this phase." | 13:44, lead, correction to the first plan | The revised plan, no commit (head `0b4ecd9`) |
| "None of the three yet. First the cheapest test, with no code change: 1. Commit the 47 Opus recordings as they are, in one commit [...] 2. Re-record with the shell's default model, claude-haiku-5-5: plain make record, no override. I will approve the prompt. 3. Run ./scripts/verify.sh eval and show me the table. [...]" | 15:11, vetting, after the Opus refusals | `827782a`, `66567b5` |

## Output review

- **Enforced.** The `Stop` hook ran lint, types and tests at the end of each agent turn.  CI ran five jobs on every pull request and push to `main`. Deny and ask rules held throughout. Auto mode's safety check blocked one command at 15:39, which wrote a config file and downloaded the gitleaks binary in one step. Not enforced: no check is marked required, because the repository is private.
- **Reported, not enforced.** The dependency audit: no finding after the two waivers.
- **By me.** I merged all five pull requests by hand, on green, and decided every review finding. I read most diffs and commit messages line by line during the build. The merges relied on green checks, the independent reviewer's reports and my decision on each finding.
- **Independent.** The reviewer subagent, once per area and once on `integration`, started with `/review-area`, given the parent spec, the child spec and the diff. Areas: 37 findings, 6 High, all High fixed. Integration: 6 findings, none High, and one point it could not verify (scanner thread safety). The built-in `/security-review` over `main...integration` reported no vulnerabilities; no finding reached its 80% confidence bar. `/code-review` was not run. Counts and decisions are in `verify.md`.
- **Caught late.** A command chain that hid the exit code let a failing check be committed in three sessions: lead (`9b3d50f`, fixed in `ffa1567`), vetting (two tier commits, fixed in `22da938`) and edge (`3c735e5`, fixed in `f6e0bd5`). The next check caught each one after the commit, not before.
- **Caught by tests and CI.** A unit test caught a provider answering for the wrong tool, which led to approval (`9e460f6`). CI caught a difference the local run missed: Typer forces colour in `--help` under `GITHUB_ACTIONS` (`500774a`).
- **By hand.** The lead session ran the break test from two fresh clones, with a script that prints each command, its output and exit code (`evidence/raw/break-test.txt`). Run 1 at `a32cf5f` found no stack trace and two unclear messages: a missing file and broken JSON gave the same message naming only the exception class, and a list with the store down and no last-good copy said "nothing can be submitted or decided". Both were fixed test first (`47f113a` red, `295941b` and `94dc6a4` green), and run 2 at `94dc6a4` confirmed them. One weak message was left as is: a JSON array as the body. This pass drove the running service with `curl` (`operate.md`).
- **Documents.** Every evidence file in this pass is written from commands run in it, including two fresh clones.

## Timeline

From the time ledger. One sitting. No phase was replayed.

| Phase | Budget | Start | End | Notes |
| --- | --- | --- | --- | --- |
| Frame and contracts | 0:00 to 0:20 | 13:38 | 14:27 | 49 minutes: setup 30, contracts 19 |
| Merge of pull request 1, worktrees, area plans | | 14:27 | 14:35 | 8 minutes |
| Build | 0:20 to 1:50 | 14:35 | 15:45 | 70 minutes, three sessions in parallel |
| Integrate and review | 1:50 to 2:25 | 15:46 | 16:23 | Break test fixes by 16:00 (`f117754`), review fixes by 16:18 (`b6a8acc`), pull request 5 merged at 16:23. Overlapped with the evidence pass |
| Evidence | 2:25 to 2:55 | 16:05 | Open until its pull request merges | A second lead session, in auto mode. First evidence commit at 16:13 |
| Clean clone | 2:55 to 3:00 | | | Fresh clones at 16:09 and after 16:17, and one on the merged state (`verify.md`) |

**Building time**: 164 minutes.

## Review findings

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

