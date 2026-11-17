---
name: open-area-pr
description: Push the current area branch and open its pull request, after the checks and the independent review. Only the user starts this.
disable-model-invocation: true
argument-hint: [area]
---
# Open the pull request for an area

Area: $ARGUMENTS

1. Confirm the branch is not `main` and the working tree is clean. If not, stop and say why.
2. Run `./scripts/verify.sh`. If any stage fails, stop. Do not open a pull request on red.
3. Confirm that `handoff/$ARGUMENTS-review.md` holds the report of `/review-area` for this branch, with the user's decision under each finding. If not, stop and ask the user to run it. Then update the session note with the `handoff` skill.
4. Push the branch. Never force push.
5. Open the pull request with `gh pr create`, base `main`. Write the body from real output only:
   - What changed, in three lines.
   - Acceptance criteria met, each with its test.
   - The summary table of the check script.
   - Review findings from that file: accepted or rejected, one line each.
   - Known gaps.
6. Watch the checks with `gh pr checks --watch`. Report the result and the link.
7. Do not merge. The user merges, with a merge commit.
