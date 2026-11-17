The change does not pass as it stands. Points 2, 3, 5 and 6 pass. Points 1, 4, 7 and 8 fail or need a decision from you.

I read `docs/specs/mcp-greenroom.md`, `docs/specs/edge.md`, `docs/structure.md` and the full diff. I also checked the installed typer exception classes and `src/mcp_greenroom/config.py`. The registry and vetting children were not needed: no file they own is in the diff. Nothing was run, so all of this comes from reading.

## Pass or fail per point

**1. Every claimed criterion has a test: FAIL (partly).**
- **Client check** passes. `tests/e2e/test_client_sim.py` covers a listed server allowed, an unlisted one blocked, an unreachable registry blocking both, an unusable reply, and paging.
- **CLI** per-command behaviour passes. Exit codes 0, 1, 2, 10 and 20, `submit --json`, plain output when piped or `NO_COLOR` is set, inert text, `--help` with one example, and no stack trace without `--debug` are all tested in `test_cli.py`, `test_cli_submit.py` and `test_cli_commands.py`.
- The part "drive every step of the demo over HTTP" fails. Its only test, `tests/e2e/test_e2e.py:18`, is skipped on this branch because `src/mcp_greenroom/api/main.py` does not exist here.
- That skip uses `pytest.importorskip`, which skips on any `ImportError`. After the merge, a broken import anywhere under `api.main` would quietly skip the end-to-end test instead of failing it. Rule: a criterion's test must run and assert, not be skippable by accident.
- The "inert description" test (`test_cli_submit.py:137`) injects the hostile text into finding `evidence` and `tool_name`, not into a tool description. That is acceptable only because the CLI never prints a description except as evidence. I am not certain the spec author meant it that way.

**2. No path approves a stopped or uncertain version: PASS.** `exit_code` (`cli_output.py:90`) gives 0 only for `"approved"`. Any other or unknown outcome gives 1. `client_sim.check_config` (`client_sim.py:98-114`) blocks everything when the registry list is unusable, and blocks any command it cannot parse (`_package` returns None, and None is never in the listed set). Two client-sim issues are in the table below. Both are spec questions rather than CLI approvals.

**3. Separation of duties enforced on the server: PASS.** The diff has no client-side check. The CLI sends the bearer token and maps the server's 403 to exit 20 (`cli_output.py:136-142`), tested in `test_cli_commands.py`. The server side is not in this diff.

**4. Rule id, no stack trace, untrusted text inert: FAIL (minor).**
- Rule ids and three-part errors pass (`cli_output.py:125-143`). Traces are hidden unless `--debug` is given (`cli_output.py:147-162`).
- Some API- or user-supplied text reaches the console without `inert()`:
  - `cli.py:261-266`: the `X-Greenroom-Generated-At` header in the `list` warning.
  - `cli_output.py:110`: the `submission_id` from the response body.
  - `cli.py:228`: the user's `submission_id` argument.
  - None of these is interpreted as markup (`Text(...)`), but control characters are not escaped.
- `--json` writes the raw API body to stdout (`cli.py:136`). JSON escapes C0 control characters but not bidi or zero-width characters. The spec says both "print the API body" and "untrusted text is printed inert". Unsure; this needs your ruling.
- On a non-2xx answer, `--json` still writes the body to stdout before the error. A non-JSON body, such as a proxy's HTML 502, breaks "one JSON document". No test covers `--json` on an error.

**5. No network in tests, no secrets: PASS.** Tests use `httpx.MockTransport` or a uvicorn server on 127.0.0.1, and the demo stays on localhost. The tokens are the documented dev stubs. One note: CLI tests call `load_settings()` (`cli.py:75`), which reads the developer's `.env`. That pulls `MCP_GREENROOM_MODEL_API_KEY` into memory and makes tests depend on local env values. Nothing prints it, but it brushes against "No test reads it". Unsure whether that counts.

**6. Audit with policy version, append-only: PASS (not touched).** The diff only reads audit data. `audit` prints `policy_version` (`cli.py:221-226`), and a test asserts it.

**7. Nothing outside the spec's scope: FAIL.**
- `.dockerignore` is not in the brief's Owns list. `handoff/edge.md:27` itself says it is "outside edge's folders", but commit 9ff3a91 added it anyway, and the handoff (state line 3, item 27) is now stale.
- Edge's own Owns list includes `briefs/area-edge.md` editing only by implication. The `cli_output.py` addition records your agreement (brief line 11), so it is fine.
- Choices the spec did not ask for:
  - `list --json` (`cli.py:254-257`) builds its own merged document, not "the API response body", and drops the degraded signal.
  - `demo.sh --fake` (`scripts/demo.sh:14,65`) runs a module from `tests/`.

**8. No test weakened: PASS, one caveat.** No existing test was changed. The only new skip is the `importorskip` at `test_e2e.py:18`, covered under point 1.

## Other items you asked for

- **Module doing more than one job:** `src/mcp_greenroom/cli_output.py`. It renders output, parses HTTP error bodies (`:114`), maps HTTP status to exit codes (`:125`) and guards against unexpected exceptions (`:147`).
- **Loosely typed boundaries:**
  - `cli.py:106` and `:129` return `Any`.
  - API bodies are used as `dict[str, Any]` and never checked against `models.Decision` or `AuditEvent` (`cli_output.py:94`, `cli.py:221`).
  - `client_sim.py:99` labels unchecked JSON as `dict[str, dict[str, Any]]`. A non-object value raises `AttributeError`, which the `except` at `cli.py:323` does not catch.
- **Errors without a usable message:** the guard at `cli_output.py:158-162` reports only the exception class name, for example "AttributeError", with no file or field. That is what a malformed client config or an unexpected response shape produces. `list` (`cli.py:243`) stops silently after 1000 pages, exits 0 and gives no warning. `client_sim` correctly treats the same case as unusable.
- **Untested failure cases:** a malformed client config, `--json` on an error, an unknown `outcome`, `list` with a repeating cursor, and a 404 for an unknown id (currently exit 1 with "Check the API log").

## Findings, most severe first

| Finding | Severity | File and line | Suggested fix |
|---|---|---|---|
| End-to-end CLI test is skipped on this branch, and `importorskip` will also skip on any later import failure | High | `tests/e2e/test_e2e.py:18` | Skip only when `importlib.util.find_spec("mcp_greenroom.api.main")` is None; otherwise import it and let failures fail. Confirm it runs at integration. |
| `.dockerignore` added outside the brief's Owns list, after the handoff called it out of scope; handoff now stale | Medium | `.dockerignore`; `handoff/edge.md:3,27` | Ask the user to approve it or hand it to the lead; update the handoff in a new commit. |
| Client sim ignores the version: an approved 1.2.0 allows any locally pinned version of that package | Medium (spec question) | `client_sim.py:31-34,110` | The spec says "match on package name and registry type", so this conforms. Confirm with the user that version-blind matching is intended. |
| Client sim parser takes the first non-flag argument. `docker run …` yields "run", so docker servers are never allowed. `uvx --from approved --with other cmd` is allowed even though another package is pulled in. `pkg==1.0` is not stripped. | Medium | `client_sim.py:37-42` | Parse per runner (the npx/uvx flags that take a value, and the image after `docker run`), and block when an extra package is named. Add tests. Unsure what Amp's documented check does here. |
| `--json` writes the raw body on errors and non-JSON answers; bidi and zero-width characters go out raw | Low to medium (unsure, spec conflict) | `cli.py:136` | Write the body only when it parses as JSON, and add a test for `--json` on 422/500. Ask the user whether `--json` must also escape hidden characters. |
| `list --json` is a merged document, not the API body, and drops the degraded flag | Low | `cli.py:254-257` | Keep it as recorded, but add a degraded marker or document it. Confirm with the user. |
| API header, response id and user argument printed without `inert()` | Low | `cli.py:228,261-266`; `cli_output.py:110` | Wrap them in `inert()`. |
| Unexpected-shape errors report only the exception class | Low | `cli_output.py:158-162`; `client_sim.py:99`; `cli.py:323` | Check the config shape and the response bodies (models) and fail with a three-part message; add a malformed-config test. |
| `list` truncates silently at 1000 pages and exits 0 | Low | `cli.py:243-253` | Detect a repeating cursor or the page cap and fail, as `client_sim._listed` does. |
| `cli_output.py` holds output, HTTP error mapping and an exception guard | Low | `cli_output.py:114,125,147` | Move the error mapping and the guard into their own module, within the 350-line limit. |
| CLI tests read the developer's `.env` through `load_settings()` | Low (unsure) | `cli.py:75` | Have the tests override `load_settings` or pass `env_file=None`. |

## User's decisions (2026-11-17), in the order of the findings table

1. End-to-end test skipped, importorskip too broad: **fix now**. Skip only when the module is absent.
2. `.dockerignore` outside the Owns list: **accept**. The user approved that one file in this session. Record it and update the stale handoff lines.
3. Client check ignores the version: **accept**. It follows the spec, which mirrors the client's documented check. Roadmap: version-aware matching.
4. Runner parsing: **fix now** the false allows. Block when a second package is named (`uvx --with`, `--from` with another command), and strip version suffixes such as `pkg==1.0`. Docker servers stay blocked (say so in the handoff); parsing `docker run` goes to the roadmap. Add tests.
5. `--json` on errors and hidden characters: `--json` prints the API body unchanged and does not escape hidden characters, because it is machine output. **Fix only**: write the body when it parses as JSON, with a test for `--json` on a 422. Last, and only if the others are green by 15:35; otherwise defer.
6. `list --json` drops the degraded flag: **defer** to the roadmap.
7. Three values printed without `inert()`: **fix now**.
8. Errors show only the exception class: **defer** to the roadmap.
9. `list` stops silently at 1000 pages: **defer** to the roadmap.
10. `cli_output.py` does several jobs: **accept**, no refactor in this slice.
11. CLI tests read the local `.env`: **fix now**; tests override `load_settings`.

Fix order: 4, 1, 7, 11, 5. Red/green TDD for each code fix.
