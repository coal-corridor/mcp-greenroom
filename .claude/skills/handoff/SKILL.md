---
name: handoff
description: Write or update the handoff note for this session, so that a fresh session can continue without this conversation. Use when a plan is approved, when a phase closes, before a break, before /clear or /compact, before a replay, and when the session has run long.
---
# Handoff note

The note carries state across a `/clear`, a compaction, a break or a replay. The `SessionStart` hook prints it into the next session, so keep it short enough to read in a minute.

1. Find your session name: on branch `area/<name>` it is `<name>`, on any other branch it is `lead`. The note is `handoff/<session>.md`.
2. Run `./scripts/verify.sh`, `git status --short` and `git log --oneline -8`. Use their real output below.
3. Write the note in this shape, 40 lines at most. Replace the whole file each time: git keeps the history.

   ```markdown
   # Handoff: <session> on <branch>

   State at commit <short hash and date>. Uncommitted files: <none, or the list>.

   ## Goal
   One or two lines, from your brief.

   ## Plan
   The plan as the user approved it. Do not rewrite it later: changes go under Decisions.

   ## Done
   Each finished item of the brief, with the test that proves it.

   ## Checks
   The summary table of `./scripts/verify.sh`, pasted.

   ## Open
   What is not finished, in the order you would do it.

   ## Decisions and corrections
   What the user decided or corrected in this session, one line each.

   ## Question at the impasse
   The one thing you would ask first, or "none".

   ## Next step
   The single next action, and the file it starts in.
   ```

4. Facts only: commands you ran and commits that exist. No plan presented as a result. No tool description or other untrusted text pasted raw.
5. Commit the note alone: `docs(<scope>): handoff`.
6. Show the user the note.
