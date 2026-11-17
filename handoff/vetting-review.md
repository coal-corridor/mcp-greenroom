I found 3 high-severity gaps, all at decision-order step 1, which a crafted submission can use to get past it. Read the code against `docs/specs/mcp-greenroom.md`, `docs/specs/vetting.md`, `docs/structure.md` and `briefs/area-vetting.md`. I did not run the test suite or `verify.sh`.

## Pass or fail per point

**1. Every claimed criterion has a test that asserts it: FAIL (partial).**
- Pass: Guarded failure (`tests/unit/test_decision_order.py:119-139`, `tests/unit/test_sample_outcomes.py:10`), Abstain with no recording (`tests/unit/test_factory.py:46`), Abstain with the classifier unavailable (`test_decision_order.py:99`), and the gate logic and per-label scanner column (`tests/unit/test_eval_gate.py`).
- Fail: vetting.md says each evaluation case runs "with a recording". No test checks that. If a case's recording is missing, the case goes to human review without notice (`evals/run_eval.py:56-71`), and the gate still passes while the share stays at or below 50%.
- Fail: the "scan did not complete" path (`src/mcp_greenroom/scanner/yara.py:61-65`, statuses `partial`, `failed`, `skipped`) has no test. `tests/unit/test_scanner_yara.py:28` only covers an exception.

**2. Nothing approves after a stop, or after a failed, missing or uncertain classifier: FAIL at step 1. Steps 2 to 8 pass.**
- Steps 2 to 8 hold. Classifier and scanner failures, junk results and unexpected errors all go to human review (`src/mcp_greenroom/vetting/pipeline.py:77-85, 210-246`), and `tests/unit/test_invariants.py` tests them.
- Step 1 ("package source not allowed") can be bypassed in three ways:
  - **`remotes` is never checked.** `src/mcp_greenroom/vetting/validation.py:96-120` only looks at `packages`. The schema allows `remotes[].url` (`contracts/server.schema.json:459`). A server with one allowed npm package plus a remote at any URL passes step 1, can be approved, and the published server.json carries that URL. Nothing handles it and nothing tests it. I am not sure whether the spec counts a remote as a "package source", but this route goes around the allowlist.
  - **npm identifiers are only checked for `://`** (`validation.py:92`). npm specs such as `github:org/repo`, `org/repo`, `file:../x` and `git@host:org/repo.git` pass. Whether a client's `npx` would then install from outside the npm registry depends on how the client uses `identifier`. I have not checked that.
  - **`runtimeArguments` and `packageArguments` are not checked.** For example `--registry=https://other.example` would pass. Same uncertainty about client behaviour.
- Step 2: `src/mcp_greenroom/vetting/rules.py:17-25` misses invisible letters outside Cf, Cc, Co and Cn: U+3164, U+FFA0, U+115F, U+1160 (category Lo) and U+2800 (So). They then reach the classifier and are not rejected by rule. This is lower risk.

**3. Separation of duties enforced on the server, from the credential: not applicable.** Nothing in the diff touches identity. No vetting code reads a caller identity.

**4. Rule id and no stack trace in errors; untrusted text never logged or printed raw: FAIL (minor).**
- Pass: every `Refusal` has a stable rule id, and the received value is escaped and truncated (`validation.py:28-38`). Logs carry only reason codes and the exception type name (`pipeline.py:80, 86-92`). Scanner text is escaped (`yara.py:25-27, 75`). Step 4's evidence is the raw description, but control characters were already rejected at step 2.
- Fail: `validation.py:74` builds `where` from `error.absolute_path` without escaping it. For maps keyed by the submitter, such as `remotes[].variables` (`server.schema.json:358-361`), the submitter's own key text goes raw into the 422 message. I worked this out from the code and did not reproduce it.
- Error surfaced without a usable message: `pipeline.py:214-215` and `pipeline.py:238-245` drop the `ScannerError` and `ClassifierUnavailable` messages and log nothing. Messages written for operators ("HTTP 401 ... check the key", "Recording does not fit ... regenerate") never reach anyone. The reasons only say "could not run" or "could not score".

**5. No network call in tests or the check script; no secret: FAIL (conditional).**
- Pass: the tests use a mock transport and the conftest guard. The scanner import is probed (`tests/unit/test_scanner_import.py`). Recordings contain no key (I searched for key and bearer patterns).
- Fail: the eval stage calls `load_settings()` (`evals/run_eval.py:143-144`) and so honours `MCP_GREENROOM_RISK_PROVIDER=live`. With that set and the key exported, as vetting.md expects for recording, `./scripts/verify.sh eval` makes live calls and gates on live answers instead of recordings. No guard runs outside pytest. Tests that build `Settings(_env_file=None)` also read the shell environment, so a set threshold changes their outcomes.

**6. Every decision carries the policy version; audit append-only: FAIL (partial).**
- Pass: every `Decision`, including the internal-error one, carries `policy_version` (`pipeline.py:262`, tested at `test_invariants.py:126`). Audit records are the registry's job and are not in this diff.
- Fail: `MCP_GREENROOM_REJECT_THRESHOLD`, `MCP_GREENROOM_APPROVE_THRESHOLD` and `MCP_GREENROOM_REQUIRE_HUMAN_FOR_ALL` (`config.py:59-62`) can change without `policy_version` changing. Two different policies then stamp the same version, so the version no longer names the policy that produced the decision. `test_policy.py` only pins `ALLOWED_SOURCES`.

**7. Nothing outside the spec's scope: FAIL (minor).**
- `src/mcp_greenroom/config.py:19-22` is "lead, frozen" (`docs/structure.md:15`) and outside the vetting brief. Approval is claimed only in the code comment and `handoff/vetting.md:33`. I cannot confirm it from the code.
- `src/mcp_greenroom/scanner/null.py` is unused. Its docstring says it fills in until the YARA adapter lands, which has happened. Dead code nobody asked for.
- `evals/run_eval.py` does four jobs: expected-outcome table, runner, report renderer and CLI. It also has a module-level dict `CAPABILITIES` (line 53) that `run_cases` fills as a side effect and `report` reads. The tests import their expectations from it.

**8. No test weakened: PASS.** All test files are new. The one looser expectation (`ambiguous-exporter` checked on outcome and tier only, `run_eval.py:38-41`) has a stated reason and is recorded as a user decision.

**Also noted, low severity:** duplicate tool names are not refused. `pipeline.py:123` builds `by_name` with the last tool winning, so step 4 at `:145` can show the wrong tool's description as "the offending text". The rejection itself is not affected.

## Findings, most severe first

| Finding | Severity | File and line | Suggested fix |
|---|---|---|---|
| `remotes[].url` skips the source allowlist; an approved record publishes any endpoint | High (unsure whether the spec counts a remote as a source) | `src/mcp_greenroom/vetting/validation.py:96-120`; `contracts/server.schema.json:459` | Refuse `remotes` (or check them against an allowlist) with `validation.source_not_allowed`, plus a test. Ask the user which. |
| npm identifier only rejects `://`; `github:`, `user/repo`, `file:` and `git@` specs pass | High (client behaviour unverified) | `validation.py:92`; tests only at `tests/unit/test_validation.py:114` | Check the identifier against the registry's package-name grammar, with one test per specifier form |
| `runtimeArguments` and `packageArguments` can redirect the registry | Medium-High (unverified) | `validation.py:83-93` | Refuse registry-override arguments, or confirm with the user that it is out of scope |
| Thresholds and require-human can change without the policy version changing | Medium | `src/mcp_greenroom/config.py:59-62`; `pipeline.py:43-49, 262` | Put the thresholds and the flag into the stamped version, or refuse non-default values unless the version changes. Raise with the lead, since config.py is frozen |
| The eval stage and the tests honour `RISK_PROVIDER=live` and env thresholds, so the check command can call the network | Medium | `evals/run_eval.py:143-144`; `tests/unit/test_sample_outcomes.py:11`; `tests/unit/test_factory.py:17` | Force replay and the default thresholds in `run_eval`, and clear `MCP_GREENROOM_*` in the tests |
| Nothing checks that every evaluation case has a recording | Medium | `tests/unit/test_eval_dataset.py` (missing); `evals/run_eval.py:56-71` | Add a test that `ReplayProvider` resolves every case tool and every sample tool except `unrecorded-reporter` |
| Scanner and classifier failure messages are dropped, nothing logged | Medium-Low | `pipeline.py:214-215, 238-245` | Log the event with the exception type and the escaped message (hashes for tool text), or put the message in the reason |
| Raw submitter keys in the schema-refusal path | Low-Medium | `validation.py:74` | Pass each path part through `escaped()` |
| Invisible letters (U+3164, U+FFA0, U+115F, U+1160, U+2800) not counted as hidden | Low-Medium | `src/mcp_greenroom/vetting/rules.py:17-25` | Add an explicit set of these code points, with tests |
| "Scan did not complete" path untested | Low | `src/mcp_greenroom/scanner/yara.py:61-65`; `tests/unit/test_scanner_yara.py:28` | Add tests that `partial`, `failed` and `skipped` raise `ScannerError` |
| Duplicate tool names allowed; wrong evidence text possible | Low | `pipeline.py:123, 145` | Refuse duplicate names at step 1 (`validation.duplicate_tool`) |
| Frozen `config.py` edited outside the area | Low (process) | `config.py:19-22` | Confirm the user's approval when merging |
| Unused `NullScanner`; `run_eval` does several jobs with a global side-effect dict | Low | `src/mcp_greenroom/scanner/null.py`; `evals/run_eval.py:31-71, 53` | Delete `null.py`; return the capabilities from `run_cases` instead of the global |

Key files:
- `/home/ilya/code/mcp-greenroom-vetting/src/mcp_greenroom/vetting/validation.py`
- `/home/ilya/code/mcp-greenroom-vetting/src/mcp_greenroom/vetting/pipeline.py`
- `/home/ilya/code/mcp-greenroom-vetting/src/mcp_greenroom/vetting/rules.py`
- `/home/ilya/code/mcp-greenroom-vetting/src/mcp_greenroom/scanner/yara.py`
- `/home/ilya/code/mcp-greenroom-vetting/src/mcp_greenroom/config.py`
- `/home/ilya/code/mcp-greenroom-vetting/evals/run_eval.py`
- `/home/ilya/code/mcp-greenroom-vetting/tests/unit/test_eval_dataset.py`

---

## User decisions, one per finding, in the order of the findings table

1. **`remotes[].url` skips the source allowlist.** Fix now. Refuse any submission with remotes in this slice, with `validation.source_not_allowed` and a test. If one of the five samples uses remotes, stop and tell the user.
2. **npm identifier only rejects `://`.** Fix now. Check the identifier against the registry's package-name grammar for npm and PyPI, one test per specifier form.
3. **`runtimeArguments` and `packageArguments` can redirect the registry.** Fix now with a short list of refused registry-override arguments and tests. Note the limit of a list for the roadmap.
4. **Thresholds and require-human change without the policy version.** Defer to integration. The lead decides, since `config.py` is frozen. Recorded as a known gap.
5. **Eval stage and tests honour live mode and env thresholds.** Fix now. Force replay and the default thresholds in `run_eval`, and clear `MCP_GREENROOM_*` in the unit tests.
6. **No check that every evaluation case has a recording.** Fix now, one test.
7. **Scanner and classifier failure messages dropped.** Fix now, last, and only if the others are green by 15:40. Otherwise defer.
8. **Raw submitter keys in the schema refusal.** Fix now.
9. **Invisible letters not counted as hidden.** Fix now, with tests.
10. **"Scan did not complete" untested.** Fix now, tests only.
11. **Duplicate tool names.** Defer to the roadmap.
12. **Frozen `config.py` edited.** Accept. The user approved that change in this session.
13. **Unused `NullScanner`, `run_eval` structure.** Accept, no refactor in this slice.

Fix order: 1, 2, 3, 5, 6, 8, 9, 10, 7.
