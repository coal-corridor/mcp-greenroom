---
name: tdd-behaviour
description: Add or change one behaviour test first, with a red commit and then a green commit. Use for every new behaviour, rule, endpoint, CLI command or bug fix in src/.
---
# One behaviour, red then green

Work on one behaviour at a time. A behaviour is one acceptance criterion, one rule or one failure path from `docs/specs/mcp-greenroom.md` or from your area's child spec in `docs/specs/`.

1. Name the behaviour in one sentence, and the criterion in the spec it serves.
2. Write the test. Assert the behaviour (status code, rule id, outcome, exit code), not the implementation.
3. Run it and confirm it fails for the right reason. A test that fails on an import error is not red yet.
4. Commit the failing test alone: `test(<scope>): <behaviour> (red)`. The scope is the one `CLAUDE.md` names for your session.
5. Write the smallest implementation that passes. No extra feature, no new dependency.
6. Run `./scripts/verify.sh test`, then the whole script.
7. Commit: `feat(<scope>): <behaviour>` or `fix(<scope>): <behaviour>`, with one line on why. Keep the default co-author trailer.

Rules:

- Never amend, rebase, squash or force push. A mistake is fixed with a new commit.
- Stay inside the folders your area brief lists.
- Tests make no network call. The classifier in a test is the replay provider or a fake.
- If the behaviour needs a contract change, a new dependency or something the spec lists as out of scope, stop and ask.
