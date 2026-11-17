# Handoff: vetting on area/vetting

State at commit b48c974 (2026-11-17, 15:20). Uncommitted files: none. Ready for /review-area.

## Goal
Given a submission, the pipeline returns the outcome the decision order demands, with evidence, for every sample and every evaluation case.

## Plan
1. Scanner fit spike, at most 10 min: cisco-ai-mcp-scanner 4.8.7 (locked) in static mode, YARA only, over the five samples' tools. Report: parseable, benign sample clean, time per run. Stop and tell the user. No fit: home-made patterns, scanner to roadmap.
2. Deterministic rules, red/green each: schema, pinned version, allowed source, tool count (Refusal, stable `validation.*` id, three-part message); hidden characters (rejected); fingerprint under reordering.
3. Decision order as one readable function in `vetting/`, one test per step 1-8, plus "provider failure never approves" and "a scanner match never approves and never rejects alone". Tiers and thresholds in `risk/`.
4. Versioned prompt, replay provider (exact hash, miss -> NoRecording), live provider over httpx, `evals/record.py` behind `make record` (user only). Scanner adapter in `scanner/`, errors -> ScannerError -> human review.
5. About 40 labelled cases in `evals/dataset*`, `evals/run_eval.py` gate and report with scanner column, sample-outcome table test. User records, then full verify and report for `evidence/verify.md`.

## Done
- All five items. Code: `vetting/` (validation, rules, policy, pipeline, factory), `risk/` (tiers, prompt, parse, replay, live, recording), `scanner/yara.py` (+ `null.py` fallback), `evals/` (dataset, gate, run_eval, record, report.md). Tests: `tests/unit/`, one file per module; decision order `test_decision_order.py`, invariants `test_invariants.py`, Abstain `test_factory.py`, sample table `test_sample_outcomes.py`, no-connection import `test_scanner_import.py`. Recordings: claude-haiku-5-5 (66567b5) in the tree; claude-opus-5-5 run kept in history (827782a). Report for `evidence/verify.md`: `evals/report.md`.

## Checks
```
  lint   pass   0.1s
  types  pass   0.2s
  test   pass   9.5s   (252 passed; YARA import ~2.5 s per process)
  eval   pass   5.4s   (24% in review, no malicious approved, scanner 6/16 malicious)
```

## Open
For the lead: `get_pipeline` should call `build_pipeline(settings)` once at startup (YARA import ~2.5 s), then reuse it.

## Decisions and corrections
- Opus run (61,891 in / 2,873 out): 17/47 refused (16 malicious + search_notes) -> review; gate failed on poisoned-notes. By label (appr/review/rej): benign 17/1/0, malicious 0/12/4, ambiguous 0/6/1.
- Haiku run (61,891 in / 6,432 out): no refusals. benign 15/3/0, malicious 0/0/16, ambiguous 0/7/0; poisoned-notes rejected at 0.97. Benign b01 lookup_fx_rate, b17 list_open_tickets tagged network_egress -> review.
- User: ambiguous-exporter checked on outcome and tier only (README fixes outcomes; it reaches review at step 5, score 0.30). Comment in `evals/run_eval.py`.
- User: `LITELLM_LOCAL_MODEL_COST_MAP` setdefault in `config.py` (4dd0c9a, approved frozen-module change); scanner adapter green 15:19, inside the 15:30 cap, not cut. Leave `pyproject.toml`; lead pins ==4.8.7. Strict `ALLOWED_SOURCES` in `vetting/policy.py`, tied to policy 2026-11-17.1; for the lead's roadmap: "allowed sources as a setting".
- Own calls: tier spans all tools of a server; offending text = tool description; replay key covers prompt hash; refusal -> review, no fallback model; recorder needs `--force` to re-record (key has no model id).

## Question at the impasse
none

## Next step
User runs /review-area.
