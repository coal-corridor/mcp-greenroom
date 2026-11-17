# Handoff: vetting on area/vetting

State at commit 09a0923 (2026-11-17). Uncommitted files: none. Pull request #4 open.

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
  test   pass   9.0s   (300 passed)
  eval   pass   4.8s   (24% in review, no malicious approved)
```

## Open
For the lead: `get_pipeline` builds `build_pipeline(settings)` once at startup (YARA import ~2.5 s). Known gaps (`handoff/vetting-review.md`): thresholds and require-human can change without the policy version (finding 4, lead decides at integration); duplicate tool names allowed (11, roadmap); the registry-override list cannot be complete (3, roadmap: build the install command ourselves).

## Decisions and corrections
- Secret scan on PR #4: gitleaks 8.30.1 `generic-api-key` flagged line 5 of all 47 recordings in 827782a, field `"key"`. False positive: the value is the replay key, a SHA-256 hex digest of prompt version, tool name and description, equal to the file name; the API key was only ever sent in a request header. User approved `.gitleaks.toml` (eedd2ca): default rules plus one allowlist, rule `generic-api-key` only, condition AND of path `^evals/recordings/[^/]+\.json$` and secret `^[0-9a-f]{64}$`.
- Opus run (61,891 in / 2,873 out): 17/47 refused (16 malicious + search_notes) -> review; gate failed on poisoned-notes. By label (appr/review/rej): benign 17/1/0, malicious 0/12/4, ambiguous 0/6/1. Haiku run (61,891 in / 6,432 out): no refusals. benign 15/3/0, malicious 0/0/16, ambiguous 0/7/0; poisoned-notes rejected at 0.97. Benign b01 lookup_fx_rate, b17 list_open_tickets tagged network_egress -> review.
- User: ambiguous-exporter checked on outcome and tier only (README fixes outcomes; it reaches review at step 5, score 0.30). Comment in `evals/run_eval.py`.
- User: `LITELLM_LOCAL_MODEL_COST_MAP` setdefault in `config.py` (4dd0c9a, approved frozen-module change); scanner adapter green 15:19, inside the 15:30 cap, not cut. Leave `pyproject.toml`; lead pins ==4.8.7. Strict `ALLOWED_SOURCES` in `vetting/policy.py`, tied to policy 2026-11-17.1; for the lead's roadmap: "allowed sources as a setting".
- Review (`handoff/vetting-review.md`): fixed 1 remotes refused, 2 npm/PyPI name grammar, 3 override args and env vars, 5 eval forces replay and default policy (unit tests clear MCP_GREENROOM_*), 6 recording coverage, 7 failure logging, 8 escaped schema path, 9 invisible letters, 10 incomplete-scan tests. Accepted: 12 config.py edit (approved this session), 13 NullScanner and run_eval kept. Own calls: tier spans all tools of a server; offending text = tool description; replay key covers prompt hash; refusal -> review, no fallback model; recorder needs `--force` to re-record (key has no model id).

## Question at the impasse
none

## Next step
The user reviews and merges the pull request (merge commit). Then the lead wires `get_pipeline`.
