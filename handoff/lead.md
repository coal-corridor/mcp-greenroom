# Handoff: lead on integration

State at commit 284e000 (2026-11-17). Uncommitted files: none except this note. Branch not pushed.

## Goal
Brief 90: the three areas work together on main, checked by the script, an independent review and a break test.

## Plan
As the user directed: wire the real pipeline, review-deferred items, vetting finding 4, roadmap, verify and demo, break test, then the user's review decisions in the order 1, 4, 3, scanner lock.

## Done
- Real pipeline built once in create_app (50caca5, 32004b2), e2e on the real app, no fakes in demo: tests/api/test_pipeline_wiring.py, tests/e2e/test_e2e.py.
- get_store returns SqlStore (b328724). Scanner pinned ==4.8.7 (3414367). One policy-version source confirmed (57027aa).
- Policy change without a new version stops startup (d4516d1): tests/shared/test_config.py.
- Break test from a fresh clone: evidence/raw/break-test.txt. Two unclear messages fixed (295941b, 94dc6a4).
- Reviews and decisions: handoff/integration-review.md (868faee). /code-review cut for time.
- Review fixes: env cleared for every test (tests/structure/test_env_isolation.py), main path "by policy" (fb0260c), pipeline build failure exits clearly (tests/failure/test_startup_pipeline.py), scanner lock (tests/unit/test_scanner_lock.py).
- ROADMAP.md: deferred review items, hash-stamped version, last-good list without a pipeline, read_submission. operate.md: scanner thread safety as a known gap.

## Checks
lint pass 0.1s, types pass 0.2s, test pass 18.4s (436 passed), eval pass 6.0s (24% in review). Exit 0. Demo exit 0, 14 of 14 steps as expected. Saved in evidence/raw/.

## Open
1. The user runs /open-area-pr integration and merges.
2. Brief 95 (evidence): README setup/run/check, verify.md from evidence/raw/, operate.md, decisions.md.

## Decisions and corrections
- The user approved the frozen config.py change (startup policy check) and accepted get_store returning SqlStore.
- Accepted gap: the policy check compares only with the defaults (ROADMAP, hash-stamped version).
- With MCP_GREENROOM_* set in the shell, test collection still reads it: api/main.py builds the app at import (registry review 9, ROADMAP).
- lead/handoff carried only this note, no evidence drafts.

## Question at the impasse
none

## Next step
Wait for the user's /open-area-pr integration, then read briefs/95-evidence.md.
