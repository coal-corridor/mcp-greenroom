# Prompts

The prompts planned for each phase. Send them as written, then save the ones actually sent, with the commit each led to, for `evidence/agentic-workflow.md`.

## Lead session

Start of the build:

> Read `docs/specs/mcp-greenroom.md`, `docs/specs/delivery.md` and `briefs/00-setup.md`. Tell me in ten lines or fewer what you will do, and list anything that looks wrong or contradictory. Do not write code until I say go.

Contracts:

> Read `briefs/10-contracts.md` and `docs/structure.md`. Propose the shared models and the seams as signatures only. Show me the list before you write any file.

Integration:

> Read `briefs/90-integrate.md`. First run `./scripts/verify.sh` on `main` and show me the table.

Evidence:

> Read `briefs/95-evidence.md`. Start with `evidence/verify.md`, from output you produce now.

## Area sessions

Opening, one per worktree (replace the area name):

> Read `docs/specs/mcp-greenroom.md`, `docs/specs/vetting.md` and `briefs/area-vetting.md`. Do not read the other child specs. Run `uv sync` and `./scripts/verify.sh quick`. Tell me your plan in five lines and wait for my go. Then save the plan with the `handoff` skill and begin with the first test. Use red/green TDD.

A feature, once one module has the right shape:

> Add the next behaviour from your brief. Follow the pattern in the file you just finished. Say how you will test it before you write it. Use red/green TDD.

## Any session

After `/clear` or a restart:

> Start from the session brief printed above. Check its handoff note against `git log`, review the changes made today, then run `./scripts/verify.sh`. If no brief was printed, read the note for this session in `handoff/` yourself.

Hands-on test, near the end of an area:

> Run the service and exercise what you built through the `mcp-greenroom` command, including one failure path. Record each command and its real output. Fix anything unclear with red/green TDD.

Break test, before packaging:

> From a fresh clone, run the setup from the README. Then run the core workflow with a missing config value, a malformed input file and the store stopped. Record each command and its output. Any stack trace or unclear message is a defect: fix it with red/green TDD.

## Hands-off runs

Optional. Use them only once a session can run without questions.

A goal, for an area session once its first module has the right shape. The evaluator reads only the transcript, so the condition names output it can see:

> /goal `./scripts/verify.sh` prints every stage as passed, and `handoff/vetting.md` lists every Deliver item of `briefs/area-vetting.md` under Done with its test

`/goal clear` cancels it. The check runs after every turn and spends tokens, so clear it when the phase closes.

A loop, for the lead session while the areas build:

> /loop check `gh pr checks` for each open pull request and report only when a check fails or all are green

`Esc` stops a self-paced loop.

## Commands only the user starts

- `/review-area` before each pull request. Then send: "Save the reviewer's report unchanged as `handoff/vetting-review.md`, add my decision under each finding, and commit it alone."
- `/open-area-pr vetting` (or `registry`, `edge`, `integration`).
- `/record-classifier` once, when the evaluation set and the samples are committed.

## Closing and replaying a phase

Close a phase, before any break:

> Use the `handoff` skill: run `./scripts/verify.sh`, write the note for this session and show it to me. It must list each item of the brief with the test that proves it, and anything not finished.

Replay a phase, in a fresh session on a new branch from `main`:

> An earlier attempt at this phase is on branch `area/vetting`. You may read it to see what went wrong. Its handoff note is `git show area/vetting:handoff/vetting.md`. Do not merge or cherry-pick from it. Start again from `briefs/area-vetting.md`. What is different this time: (say what changed in the prompt, the brief or `CLAUDE.md`).

## Steering rules for the user

- Start each session in plan mode, read the plan, then switch to accept edits. Deny rules hold in every mode. Never bypass permissions.
- Watch the first minute of each task. `Esc` stops it.
- After two failed corrections, `/clear` and write a better prompt. Do not try a third.
- The second time a mistake repeats, add one line to `CLAUDE.md` or one check to the script, in its own commit with a message that says why. While the three areas run in parallel, edit `CLAUDE.md` on `main` only, from the lead session: an area session records the correction in its handoff note, under "Decisions and corrections", because three branches that edit the same file conflict at merge.
- After any edit to `CLAUDE.md`, run `/memory` to see which instruction files are loaded, or `/context all` to see the whole context window.
- Never a bare `/compact`. Say what to keep, or better: the `handoff` skill, then `/clear`.
- Two tells in one session (sloppier edits, missed cases, reflexive agreement): `handoff`, `/clear`, continue from the note. Do not push through.
- Review from the diff, not from the summary: the files in the plan first, then anything outside it.
- Commit before every risky step.
- Close each phase before a break, and write the start and stop times in the time ledger. A replayed phase counts in full.
- Log each stop, rewind, restart and scope cut in `evidence/session-log.md`, with the time and the reason.
- Read every diff and every commit message before it reaches `main`.
