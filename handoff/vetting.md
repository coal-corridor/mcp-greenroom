# Handoff: vetting on area/vetting

State at commit 2ca2349 (2026-11-17). Uncommitted files: none.

## Goal
Given a submission, the pipeline returns the outcome the decision order demands, with evidence, for every sample and every evaluation case.

## Plan
1. Scanner fit spike, at most 10 min: cisco-ai-mcp-scanner 4.8.7 (locked) in static mode, YARA only, over the five samples' tools. Report: parseable, benign sample clean, time per run. Stop and tell the user. No fit: home-made patterns, scanner to roadmap.
2. Deterministic rules, red/green each: schema, pinned version, allowed source, tool count (Refusal, stable `validation.*` id, three-part message); hidden characters (rejected); fingerprint under reordering.
3. Decision order as one readable function in `vetting/`, one test per step 1-8, plus "provider failure never approves" and "a scanner match never approves and never rejects alone". Tiers and thresholds in `risk/`.
4. Versioned prompt, replay provider (exact hash, miss -> NoRecording), live provider over httpx, `evals/record.py` behind `make record` (user only). Scanner adapter in `scanner/`, errors -> ScannerError -> human review.
5. About 40 labelled cases in `evals/dataset*`, `evals/run_eval.py` gate and report with scanner column, sample-outcome table test. User records, then full verify and report for `evidence/verify.md`.

## Done
- `uv sync` and `./scripts/verify.sh quick` run in this worktree: green.
- Found: fingerprint stability under reordering already exists in contracts (`tests/shared/test_fingerprint.py`, commit caae224).

## Checks
```
  stage  result time
  lint   pass   0.1s
  types  pass   0.2s
  test   pass   1.2s
  eval   skip   0.0s
```

## Open
Plan items 2 to 5, then the scanner adapter and config change (moved to the end).

## Decisions and corrections
- User approved the five-line plan.
- Spike (14:36): scanner fits. Parseable, benign clean, poisoned-notes/search_notes 2 HIGH, <1 ms/scan, 2.5 s import. Import loads litellm, which fetches a remote cost map: 8 connect attempts; `LITELLM_LOCAL_MODEL_COST_MAP=True` stops them.
- User: set that var in `config.py` with `os.environ.setdefault`, own commit, with a test that importing the adapter makes no connection. Approved change to the frozen module, this branch only.
- User: leave `pyproject.toml`; the lead pins ==4.8.7 at integration.
- User: scanner adapter and the config change come LAST, after the eval gate. Until then use a no-findings scanner on the seam. Adapter is first to cut.

## Question at the impasse
none

## Next step
Validation rules, red/green each, starting in `tests/unit/`.
