# Handoff: vetting on area/vetting

State at commit 827782a (2026-11-17). Uncommitted files: none.

## Goal
Given a submission, the pipeline returns the outcome the decision order demands, with evidence, for every sample and every evaluation case.

## Plan
1. Scanner fit spike, at most 10 min: cisco-ai-mcp-scanner 4.8.7 (locked) in static mode, YARA only, over the five samples' tools. Report: parseable, benign sample clean, time per run. Stop and tell the user. No fit: home-made patterns, scanner to roadmap.
2. Deterministic rules, red/green each: schema, pinned version, allowed source, tool count (Refusal, stable `validation.*` id, three-part message); hidden characters (rejected); fingerprint under reordering.
3. Decision order as one readable function in `vetting/`, one test per step 1-8, plus "provider failure never approves" and "a scanner match never approves and never rejects alone". Tiers and thresholds in `risk/`.
4. Versioned prompt, replay provider (exact hash, miss -> NoRecording), live provider over httpx, `evals/record.py` behind `make record` (user only). Scanner adapter in `scanner/`, errors -> ScannerError -> human review.
5. About 40 labelled cases in `evals/dataset*`, `evals/run_eval.py` gate and report with scanner column, sample-outcome table test. User records, then full verify and report for `evidence/verify.md`.

## Done
- Items 1-4: `vetting/validation.py`, `rules.py`, `pipeline.py` (steps 1-8), `factory.py`; `risk/` tiers, prompt `classifier-v1.md`, parse, replay, live; recorder `evals/record.py` (stops when its first call fails). Tests in `tests/unit/`, one file per module (decision order `test_decision_order.py`, invariants `test_invariants.py`, Abstain `test_factory.py`). Fingerprint reorder: `tests/shared/test_fingerprint.py`.
- Item 5: `evals/dataset.jsonl` (41: 18 benign, 16 malicious, 7 ambiguous), `evals/gate.py`, `evals/run_eval.py`. Opus recordings committed (827782a).

## Checks
```
  lint   pass   0.1s
  types  pass   0.2s
  test   pass   0.8s   (246 passed)
  eval   FAIL   0.3s   (Opus run: poisoned-notes lands in review, see below)
```

## Open
(1) Re-record with claude-haiku-5-5 (`--force`), `./scripts/verify.sh eval`; stop if Haiku refuses too. (2) If the gate passes and poisoned-notes is rejected: commit Haiku recordings, sample-table pytest, save eval report. (3) Scanner adapter + `config.py` setdefault commit.

## Decisions and corrections
- Run 1, claude-opus-5-5, prompt classifier-v1 (sha256:0557a8c72c79): 47 recorded, 61,891 tokens in, 2,873 out. 17 of 47 refused (stop_reason refusal, 0 output tokens): all 16 malicious + search_notes. Refusal -> classifier.unavailable -> human review. Gate FAIL on poisoned-notes only; no malicious approved; 19/41 (46%) in review, warning.
- Run 1 by label (approved/review/rejected): benign 18: 17/1/0 (review = tier.medium); malicious 16: 0/12/4 (rejected = hidden chars); ambiguous 7: 0/6/1 (rejected = score). Samples as table except poisoned-notes (review, expected rejected).
- User: keep run 1 committed as the record; try claude-haiku-5-5 next, no code change. Fallbacks and stop_details: not yet.
- Own calls: tier spans all tools of a server (union); offending text = tool description; key covers prompt hash; refusal -> review. Spike: scanner fits (benign clean, poisoned-notes 2 HIGH, <1 ms/scan, 2.5 s import); its import fetches a litellm cost map, stopped by `LITELLM_LOCAL_MODEL_COST_MAP=True`.
- User: set that var in `config.py` with `os.environ.setdefault`, own commit, with a test that importing the adapter makes no connection (approved change to the frozen module). Leave `pyproject.toml`; lead pins ==4.8.7.
- User: strict `ALLOWED_SOURCES` in `vetting/policy.py`, tied to policy 2026-11-17.1; roadmap "allowed sources as a setting". Scanner adapter and config change LAST, after the eval gate; NullScanner until then; adapter first to cut.

## Question at the impasse
none

## Next step
Re-record with Haiku: `uv run python -m evals.record --force` (the shell's model), then `./scripts/verify.sh eval`.
