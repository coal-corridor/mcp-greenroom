---
name: verify-change
description: Check a change before saying it is done. Use after any edit to code, tests, scripts, CI or sample data, and before every commit, hand-back or pull request.
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/test-changes.sh *)
---
# Verify a change

1. Run `./scripts/verify.sh`. For a quick loop, run one stage first (`./scripts/verify.sh quick`, `test` or `eval`), then the whole script before you finish.
2. If a stage fails, read the first error, fix the cause and run it again. Do not weaken or delete a test to get green. Do not edit a recording.
3. Read the diff, not your memory of it: `git status --short`, `git diff main...HEAD --stat`, then the changed files. Name any file outside the folders your brief lists.
4. Run `${CLAUDE_SKILL_DIR}/scripts/test-changes.sh main`. For every removed assertion, new skip or xfail marker and removed test it lists, say why it is right, or restore it.
5. If the change touches the API or the CLI, exercise it for real: start the service, run the command or `curl` call that shows the new behaviour, and one call that shows its failure path. Stop the service afterwards.
6. Report in this shape, using output you actually produced:
   - Commands run, each with its exit code and the last lines of its output.
   - Acceptance criteria from `docs/specs/mcp-greenroom.md` or your area's child spec that this change meets, each with the test that proves it.
   - Tests changed, from step 4, with the reason for each.
   - What is not finished or not verified.

Never write "tests pass" without the output above it. If something was not run, say that it was not run.
