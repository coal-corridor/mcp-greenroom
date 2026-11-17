# Brief 90: integrate

Session: lead, on `main` and one short branch `integration`. Budget: 35 minutes.

## Goal

The three areas work together on `main`, checked by the script, by an independent review and by a person breaking it on purpose.

## Steps

1. The user merges the pull requests in this order: vetting, registry, edge. Each needs green required checks and an answered review.
2. On branch `integration`: wire the real pipeline, provider and scanner in at the injection point. Replace fakes in the end-to-end test.
3. Run `./scripts/verify.sh`. Fix seams with the `tdd-behaviour` skill.
4. The user runs `/review-area`, then the built-in `/security-review` and `/code-review` on the same branch. Record each finding and the decision on it, with the command that produced it, in `handoff/integration-review.md`.
5. Run `./scripts/demo.sh` and save its real output.
6. Break it on purpose, from a fresh clone: follow the README setup, then run the core workflow with a missing config value, a malformed input file and the store stopped. Record each command and its output. A stack trace or an unclear message is a defect: fix it test first.
7. The user runs `/open-area-pr integration` and merges.

## Stretch, only if all of the above is green

In the spec's cut order, last first: the shadowing rule, the per-version endpoints, the interactive menu, upstream references, tracing. The user picks. One at a time, each test first. Read `docs/specs/stretch.md` only at this point, and build from the section of the item picked.

## Done when

`./scripts/verify.sh` is green on `main`, the required checks are green on its last commit, and the demo output and the break test are saved for `evidence/verify.md`.

## Stop and ask

The check script is still red with 35 minutes left. Cut scope then, and record the cut in `evidence/decisions.md`.
