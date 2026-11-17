# Handoff: vetting on area/vetting

State at commit ae84c4c (2026-11-17). Uncommitted files: none.

## Goal
Given a submission, the pipeline returns the outcome the decision order demands, with evidence, for every sample and every evaluation case.

## Plan
1. Scanner fit spike, at most 10 min: cisco-ai-mcp-scanner 4.8.7 (locked) in static mode, YARA only, over the five samples' tools. Report: parseable, benign sample clean, time per run. Stop and tell the user. No fit: home-made patterns, scanner to roadmap.
2. Deterministic rules, red/green each: schema, pinned version, allowed source, tool count (Refusal, stable `validation.*` id, three-part message); hidden characters (rejected); fingerprint under reordering.
3. Decision order as one readable function in `vetting/`, one test per step 1-8, plus "provider failure never approves" and "a scanner match never approves and never rejects alone". Tiers and thresholds in `risk/`.
4. Versioned prompt, replay provider (exact hash, miss -> NoRecording), live provider over httpx, `evals/record.py` behind `make record` (user only). Scanner adapter in `scanner/`, errors -> ScannerError -> human review.
5. About 40 labelled cases in `evals/dataset*`, `evals/run_eval.py` gate and report with scanner column, sample-outcome table test. User records, then full verify and report for `evidence/verify.md`.

## Done
- Items 1-2: spike; step 1 `vetting/validation.py` (`validation.version_not_pinned`, `.schema`, `.source_not_allowed`, `.no_tools`); step 2 `vetting/rules.py` (`rule.hidden_characters`). Fingerprint reorder test already in `tests/shared/test_fingerprint.py`.
- Item 3: `vetting/pipeline.py` steps 1-8 (`tests/unit/test_decision_order.py`), invariants (`test_invariants.py`), tiers `risk/tiers.py`, `vetting/factory.py` + Abstain on the real sample (`test_factory.py`).
- Item 4: prompt `risk/prompts/classifier-v1.md` + key (`test_prompt.py`), parser, replay, live over httpx (`test_parse/replay/live.py`), recorder `evals/record.py` (`test_record.py`). Scanner: `scanner/null.py` stand-in. Item 5: `evals/dataset.jsonl` (41: 18 benign, 16 malicious, 7 ambiguous), `evals/gate.py`, `evals/run_eval.py` with the sample table.

## Checks
```
  lint   pass   0.1s
  types  pass   0.3s
  test   pass   1.1s   (243 passed)
  eval   FAIL   0.5s   (expected: no recordings yet, 37/41 in review)
```

## Open
(1) User runs /record-classifier (47 tools), then `./scripts/verify.sh eval`; stop and ask if a sample misses or the gate fails. (2) Sample-table pytest on real recordings; save the eval report for `evidence/verify.md`. (3) Scanner adapter (YARA static) + `config.py` setdefault commit with the no-connection import test.

## Decisions and corrections
- Own calls: tier spans all tools of a server (union); offending text = the tool description; key also covers prompt hash; refusal -> review, no fallback model. User approved the five-line plan. Spike (14:36): scanner fits. Parseable, benign clean, poisoned-notes/search_notes 2 HIGH, <1 ms/scan, 2.5 s import. Import loads litellm, which fetches a remote cost map: 8 connect attempts; `LITELLM_LOCAL_MODEL_COST_MAP=True` stops them.
- User: set that var in `config.py` with `os.environ.setdefault`, own commit, with a test that importing the adapter makes no connection. Approved change to the frozen module, this branch only. Leave `pyproject.toml`; the lead pins ==4.8.7 at integration.
- User: strict allowed sources kept as `ALLOWED_SOURCES` in `vetting/policy.py`, pinned to policy version 2026-11-17.1; config.py unchanged. For the lead: roadmap "allowed sources as a setting". User: scanner adapter and the config change come LAST, after the eval gate. Until then use a no-findings scanner on the seam. Adapter is first to cut.

## Question at the impasse
none (waiting on the user's recording run)

## Next step
Wait for the recordings, then `./scripts/verify.sh eval`.
