# Handoff: lead on setup

State at commit f343f5d (2026-11-17). Uncommitted files: none. PR #1 (setup -> main) open.

## Goal
Brief 00: check script, PR checks, guard rails (closed). Brief 10: shared shapes and seams written, tested, frozen; same PR.

## Plan
Brief 00 as approved: pyproject/lock, verify.sh, network guard, structure tests, ci.yml, Makefile.
Brief 10, one commit each: contracts/, shared modules, seams, sample-data/servers, fakes under tests/, one shape test per shared module, CLAUDE.md paths.

## Done
- 86697af pyproject, uv.lock, .python-version, empty package.
- 0be6efe scripts/verify.sh. 0e67edf network guard (tests/structure/test_network_guard.py). 9b3d50f + ffa1567 structure rules (tests/structure/test_source_rules.py).
- b07f740 ci.yml, 40070b0 Makefile. CI run 44008340480 on PR #1: all five jobs green and named.
- f343f5d contracts/: OpenAPI 2025-12-01 and server.schema.json 2025-12-11 pinned with sha256. Match the spec.

## Checks
  lint   pass   types  pass   test   pass (17)   eval   skip   (exit 0, before f343f5d; quick green after it)

## Open
1. Propose model names and fields plus seams. The user decides.
2. Brief 10 items 2 to 7. 3. "contracts frozen", green checks, user merges PR #1.

## Decisions and corrections
- The repo is private, so required checks are off. The user merges on green by hand.
- No baseline commit (main had 3 commits).
- cisco-ai-mcp-scanner kept. litellm GHSA-g5ff-637f-6q2m and GHSA-7hp6-4w63-5g45 waived in [tool.uv.audit], recorded in evidence/decisions.md (user's choice).
- Secret scan: pinned gitleaks 8.30.1 binary over full history, not the official action (that scans only the event's commits). Departs from delivery.md.
- The user said: stop researching gitleaks, decide with what is known.
- ruff 0.17 also formats Python code blocks in .md files, so lint covers docs.
- Check verify.sh's own exit code before a commit (9b3d50f slipped through `| tail`).

## Question at the impasse
Model names and fields and the injection approach: waiting for the user.

## Next step
Write src/mcp_greenroom/models.py once the user approves the proposal.
