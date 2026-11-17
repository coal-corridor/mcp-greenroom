# Integration review: branch integration

Three reviews on branch `integration` at f117754, 2026-11-17. The user's decision follows each finding.

## /review-area

The reviewer's report, unchanged. The user's decisions are added in the blocks starting **Decision (user)**.

I found no failure on safety points 2 to 8. Point 1 passes with one weak assertion and two untested error branches. The most serious gap is in point 5: three test folders read the developer's shell settings, so with the recording-run shell they would read the API key.

### Pass or fail per point

**1. Every claimed acceptance criterion has a test: pass, with gaps.**
- Main path through the real pipeline: `tests/api/test_pipeline_wiring.py:50-61`.
- Policy change without a new version stops startup: `tests/shared/test_config.py:62-77`.
- List with no store and no last-good copy: `tests/failure/test_list_without_snapshot.py:16-30`.
- Missing file and broken JSON in the CLI: `tests/e2e/test_cli_submit.py:182-197`.
- Weak assertion: the spec says "approved by policy", but the test only checks that outcome is approved and that `reasons` is not empty (`test_pipeline_wiring.py:57-58`). It does not check `decided_by == "policy"` or the reason code `policy.tier_low`.
- No test for two branches of the new input reader: the non-UTF-8 file and the other read errors (`src/mcp_greenroom/cli_input.py:28-37`).

**2. Nothing approves after a rule, scanner or classifier stop: pass.** The diff adds no approval path. In `vetting/factory.py:12`, the live provider falls back to replay when the key is missing, but `config.py:73-77` rejects that setup at startup, so the fallback can't run. If the pipeline fails to build, the service doesn't start, so nothing is approved (finding 3).

**3. Separation of duties is enforced on the server: pass.** `get_identity` did not change. The end-to-end test now runs the real pipeline, and its own-review and other-reviewer steps cover this (`tests/e2e/test_e2e.py:102-105`).

**4. Errors have a rule id, no stack trace, no raw untrusted text: pass.** The new 503 carries `store.unavailable` (`api/routers/servers.py:50-55`). The log line holds only the exception class name. CLI input errors print through `fail()`, which prints inert (`cli_output.py:41-48`).

**5. No network call, no secret: pass, with a caveat.** The socket guard in `tests/conftest.py:57-78` blocks any call to a non-local address. The pin `cisco-ai-mcp-scanner==4.8.7` is what `vetting.md` asks for. The diff has no secret. The caveat is finding 1.

**6. Every decision has an audit record with the policy version, and no update or delete: pass, with a known gap.** `test_pipeline_wiring.py:64-82` shows that refusals and decisions take the version from one source. The diff does not touch the store's append-only path. The gap is finding 2.

**7. Nothing out of scope: pass.** The evidence files, the ROADMAP, the scanner pin and dropping `--fake` from the demo all fit the integration phase. One structural choice was not asked for (finding 5).

**8. No test weakened: pass.**
- The module-level skip in `test_e2e.py` was removed, which makes the test stricter.
- `test_eval_settings.py` gains a `setenv` for the policy version, with its reason in a comment, and one more assertion.
- `fake_service.py` was a helper, not a test.

### Findings

**1. Tests in `tests/api`, `tests/e2e` and `tests/failure` read the shell's settings.**
- Rule: CLAUDE.md says no test reads `MCP_GREENROOM_MODEL_API_KEY`, and tests must run with no credentials.
- These tests build `Settings(_env_file=None, ...)` without clearing `MCP_GREENROOM_*` variables:
  - `tests/api/test_pipeline_wiring.py:22,67`
  - `tests/e2e/test_e2e.py:32-40`
  - `tests/failure/test_list_without_snapshot.py:17`
- Before this change it didn't matter, because every test used the fake pipeline. Now the real pipeline is built from those settings.
- So in a shell set up for the recording run (live provider, model and key set), these tests load the real key and build the live provider. The socket guard stops the call, so the key does not leave the machine, but the tests fail or pass depending on the shell.
- A shell that has changed a threshold also makes them crash on the new policy-version check.
- `tests/unit/conftest.py` and `tests/shared/test_config.py:10-16` already clear these variables. `evals/run_eval.py:138-152` handles the same risk on purpose.

> **Decision (user):** fix now. Move the clearing fixture up to `tests/conftest.py`.

**2. The policy version only has to change when a setting moves away from its default.**
- Rule: the parent spec says every decision carries the policy version that produced it.
- The check at `src/mcp_greenroom/config.py:78-88` compares only with the defaults. Once a custom version is set (say `.2` with a reject threshold of 0.9), changing the threshold again to 0.95 starts without complaint. Two different policies then share one version in the audit trail.
- This is already listed in `ROADMAP.md` ("Deferred from the area reviews", vetting review 4). I am raising it because the invariant is still only partly met.

> **Decision (user):** accept as a known gap. It is already on the roadmap with the hash-stamped version.

**3. A pipeline that fails to build at startup is not handled.**
- Rules: CLAUDE.md says an error leads with what failed, what was received and what to do. The interface contract says a scanner failure fails closed to human review.
- `src/mcp_greenroom/api/main.py:46` calls `build_pipeline(settings)` outside any `try`. If the scanner fails to import, uvicorn prints a traceback with no next step.
- Because this runs before the store is set up, a scanner failure also takes down degrade mode: the last-good list is not served.
- This fails safe, since nothing gets approved, but the message is not usable and no test covers it.

> **Decision (user):** fix now, the small version: catch it and exit with what failed, what was received and what to do, with a test. Put "keep serving the last-good list when the pipeline cannot be built" on the roadmap.

**4. The main path test does not check "by policy".** See point 1 (`tests/api/test_pipeline_wiring.py:57-58`).

> **Decision (user):** fix now.

**5. `get_store` now returns the concrete store class, not the shared interface.**
- Rule: a structural choice the spec did not ask for, made in a file whose docstring says "Frozen names and return types" (`src/mcp_greenroom/api/dependencies.py:3,28-31`).
- The recorded decision was different: `handoff/registry-review.md:96-97` says "the lead fills the `Store` protocol". The diff took the review's other option instead.
- `interfaces.Store` (`src/mcp_greenroom/interfaces.py:74-79`) is now used nowhere, and its docstring is out of date.

> **Decision (user):** accept the option taken. Correct the stale docstring. Changed decision: registry review item 8 recorded "the lead fills the `Store` protocol"; at integration the user directed "fill the Store protocol or return SqlStore from get_store", the lead returned `SqlStore`, and the user accepts that here. `interfaces.Store` stays unused.

**6. The CLI input reader has untested branches and a loose return type.**
- `read_submission` returns `Any` (`src/mcp_greenroom/cli_input.py:15`). Its docstring says it reads a submission file, but it never checks that the file holds a JSON object. A JSON array goes to the API and comes back as the generic "Request failed validation at body". The break test already recorded this as weak.
- Nesting deep enough to hit Python's recursion limit raises `RecursionError`, which no branch catches, so the user may see a traceback. I have not run this case. It was also uncaught before this change.
- Lines 28-37 (non-UTF-8 file and other read errors) have no test.

> **Decision (user):** defer to the roadmap.

### Not verified

- The scanner is now built once and shared across all requests, which FastAPI runs on several threads (`api/main.py:46`). I did not check whether the scanner package's `StaticAnalyzer` is safe to share between threads. Someone should confirm.

> **Decision (user):** put a lock around the shared scanner call in the adapter, and list the scanner's thread safety as not verified in the known gaps for `operate.md`.

### Summary table

| Finding | Severity | File and line | Suggested fix |
|---|---|---|---|
| api, e2e and failure tests read `MCP_GREENROOM_*` from the shell, including the key, now that the real pipeline is wired | Medium | `/home/ilya/code/mcp-greenroom/tests/api/test_pipeline_wiring.py:22,67`; `/home/ilya/code/mcp-greenroom/tests/e2e/test_e2e.py:32-40`; `/home/ilya/code/mcp-greenroom/tests/failure/test_list_without_snapshot.py:17` | Move the env-clearing fixture from `tests/unit/conftest.py` up to `tests/conftest.py`, or pass `risk_provider="replay", model_api_key=None` explicitly |
| Policy version is checked only against the defaults, so two policies can share one version | Medium (already in the ROADMAP) | `/home/ilya/code/mcp-greenroom/src/mcp_greenroom/config.py:78-88` | Stamp the version with a hash of the thresholds and the require-human flag (the ROADMAP item) |
| Pipeline build failure at startup gives a traceback and also loses degrade mode; no test | Low to Medium | `/home/ilya/code/mcp-greenroom/src/mcp_greenroom/api/main.py:46` | Catch it and exit with what failed, what was received and what to do. Or keep the store up and have `get_pipeline` refuse with 503 and a rule id. Add a test |
| Main path test does not check "approved by policy" | Low | `/home/ilya/code/mcp-greenroom/tests/api/test_pipeline_wiring.py:57-58` | Assert `decided_by == "policy"` and the reason code `policy.tier_low` |
| `get_store` return type changed in a file marked frozen, against the recorded decision; `Store` protocol now unused | Low | `/home/ilya/code/mcp-greenroom/src/mcp_greenroom/api/dependencies.py:3,28-31`; `/home/ilya/code/mcp-greenroom/src/mcp_greenroom/interfaces.py:74-79` | Get the user's agreement and update or remove the `Store` protocol, or fill the protocol as decided |
| `read_submission` returns `Any` and does not check for a JSON object; non-UTF-8 and other read-error branches untested; `RecursionError` not caught | Low | `/home/ilya/code/mcp-greenroom/src/mcp_greenroom/cli_input.py:15,28-37` | Check for a dict and raise `InputError`, type the return as `dict[str, Any]`, and add tests for the other branches |

User's fix order: 1, 4, 3, then the scanner lock. Red then green for each code fix.

## /security-review

Run by the user on branch `integration` at f117754, 2026-11-17 16:05, over `main...integration`.

Result: no vulnerabilities reported. No finding reached the 80% confidence bar, so there was nothing to filter.

What it checked:
- `get_pipeline` (`src/mcp_greenroom/api/dependencies.py`): one pipeline, built at startup and shared by every request. It keeps no state between requests, and identity still comes from the credential through the unchanged `get_identity`.
- Startup (`src/mcp_greenroom/api/main.py`): the model API key is used only to build the live provider, never logged or returned. Replay is the default, and live mode needs both a model and a key.
- New 503 on the list (`src/mcp_greenroom/api/routers/servers.py`): a fixed message in the response. The error text goes only to the server log.
- Reading a submission file (`src/mcp_greenroom/cli_input.py`, `src/mcp_greenroom/cli.py`): a path the CLI's own user passes, parsed with `json.loads` only. Errors show the path, the JSON error with line and column, or the OS error, never the file's contents.
- Policy-version startup check (`src/mcp_greenroom/config.py`): makes startup stricter and fails closed. The message names only variables and the version.
- `evals/run_eval.py`: pins the eval to the default policy version. No security effect.
- `scripts/demo.sh`: arguments are refused, not used in commands. The service binds to 127.0.0.1, and the data folder comes from `mktemp -d`.
- `pyproject.toml`, `uv.lock`: `cisco-ai-mcp-scanner` pinned to 4.8.7.
- Not counted as findings: the stub tokens `dev-dana`, `dev-riley` and `dev-sam` in `evidence/raw/`, synthetic dev-only identities by design.

## /code-review

Not run. Cut for time by the user.
