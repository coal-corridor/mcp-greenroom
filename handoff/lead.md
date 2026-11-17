# Handoff: lead on lead/handoff

State at commit 2ca2349 (2026-11-17), the merge of PR #1 into main. Uncommitted files: none except this note.

## Goal
Briefs 00 (check script, PR checks, guard rails) and 10 (shared shapes and seams, frozen) are both closed. Next lead phase: brief 90, integration, once the area PRs land.

## Plan
As approved: brief 00 items 1 to 6, then brief 10 items 1 to 7, in one setup PR. Corrections are under Decisions.

## Done
- PR #1 merged as 2ca2349. CI run 44010204313 on 3e8f6e6: verify (quick|test|eval), secret scan and dependency audit all green.
- Brief 00 tests: tests/structure/test_network_guard.py, tests/structure/test_source_rules.py.
- contracts/: OpenAPI 2025-12-01 and server.schema.json 2025-12-11, pinned with sha256 (f343f5d).
- Red then green, tests in tests/shared/: config (test_config.py, 2c75fb4), logging (test_logging.py, 266530f), fingerprint (test_fingerprint.py, caae224). Models aa22957, seams 8502a91.
- sample-data/servers/: five samples plus an outcomes table (test_samples.py, 0eea3c2). Fakes: tests/fakes.py (test_fakes.py, 4dc232d).
- CLAUDE.md line 24 names config.py and log_event (68cf5a3).

## Checks
lint pass 0.7s, types pass 0.3s, test pass 0.7s (43 passed), eval skip 0.0s. Exit 0 on main at 2ca2349.

## Open
1. Wait for the area PRs (vetting, registry, edge). Review each against its spec with the reviewer agent.
2. Brief 90 (integration), then brief 95 (evidence).
3. When the repo goes public, the user makes verify (quick|test|eval) and secret scan required checks.

## Decisions and corrections
- The repo is private. The user merges on green by hand. litellm advisories waived in [tool.uv.audit] (fabf418). Secret scan runs the pinned gitleaks 8.30.1 binary, not the action. delivery.md updated and decisions.md has a record (a6b4466).
- Env names follow .env.example (RISK_PROVIDER, MODEL). recordings_dir defaults to evals/recordings.
- Contracts frozen on 2026-11-17 at 3e8f6e6. unrecorded-reporter is excluded from the recording run (vetting.md and the record-classifier skill).
- The schema refuses `latest` only on packages[].version. Vetting needs its own rule for the top-level version.
- Not checked by tooling: mypy does not cover tests/, so nothing checks that the fakes match the protocols.
- Check verify.sh's own exit code before every commit (9b3d50f slipped through `| tail`, fixed in ffa1567).

## Question at the impasse
none

## Next step
Read briefs/90-integrate.md once the first area PR is open, and review that PR with the reviewer agent.
