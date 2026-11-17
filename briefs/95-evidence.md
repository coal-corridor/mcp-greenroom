# Brief 95: evidence and packaging

Session: lead. Budget: the last 30 minutes of the build, then the packaging window.

## Goal

A reader can understand, run and question the slice from the README and six one-page files, and every claim in them was produced by a command.

## Steps

1. Use the `write-evidence` skill. Fill the files in this order: `verify.md`, `operate.md`, `design.md`, `README.md`, `agentic-workflow.md`, `decisions.md`. Sources for `agentic-workflow.md`: `evidence/session-log.md`, the notes and review reports in `handoff/`, and the commit history.
2. `verify.md` first, because the rest cites it: the check script table, the evaluation report with the scanner column, the demo output, the break test, the link to the last run of the pull request checks, the audit result, the local versus pipeline table, known gaps. The table of criteria and tests covers `docs/specs/mcp-greenroom.md` and every child spec in `docs/specs/`. Leave out `stretch.md` unless a stretch item was built.
3. Draft only the factual parts of `decisions.md` and `intent.md`. The user writes the trade-offs and assumptions in their own words. Then proofread, and change nothing in meaning.
4. Replace every `TODO(build)` marker. If only the user knows the answer, ask. Do not guess.
5. Remove any claim that the check script or a test does not actually prove.
6. From a fresh clone in a new directory: follow the README, run `./scripts/verify.sh`, run `./scripts/demo.sh`. Paste the result.

## The user does

- Reads the README and all six files line by line.
- Fills the timeline, the prompts as sent and the interventions from `evidence/session-log.md`.
- Confirms what was prepared in advance, including any template that was copied.
- Checks that the exercise brief itself is nowhere in the repo.

## Done when

No `TODO(build)` is left, the fresh clone is green, and the submission note holds the repo link, any setup note beyond the README, the time spent and the tools used.
