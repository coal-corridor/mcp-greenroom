---
name: record-classifier
description: Produce the classifier recordings with one live model run. Uses the network and an API key, so only the user starts it.
disable-model-invocation: true
---
# Record the classifier

This is the only step of the build that calls a model.

Before:

1. The evaluation set and the sample servers are committed.
2. The key variable is set in the shell. Check that it is set without printing its value. If it is missing, stop.
3. The prompt file carries a version, and the working tree is clean.

Run:

4. `make record`. It sends every evaluation sample and every sample tool except those of `unrecorded-reporter` (which must stay unrecorded for the Abstain criterion) through the live provider and writes one recording per tool to `evals/recordings/`, with model id, prompt hash, token counts and time.
5. `./scripts/verify.sh eval`.

After:

6. If a sample lands on the wrong outcome, change the wording of the sample, never the recording, and record again. Say which samples changed and why.
7. If the evaluation gate fails, report the table and stop. Only the user changes a threshold, with a record in `evidence/decisions.md`.
8. Commit the recordings in one commit: `data(vetting): classifier recordings (<model id>, prompt <version>)`.
9. Save the evaluation table for `evidence/verify.md`.

Never write or edit a recording by hand. Never print, log or commit the key. If the run cannot be completed, stop and tell the user. The fallback is the user's decision.
