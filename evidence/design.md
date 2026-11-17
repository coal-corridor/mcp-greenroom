# Design: MCP Greenroom

Written from the code at commit `f117754`. Background and sources are in `docs/spec-notes.md`. Nothing here was deployed.

## Architecture

One Python service and one CLI, in one package (`src/mcp_greenroom/`, 3,258 lines of Python).

```text
mcp-greenroom CLI ──HTTP──▶ API (FastAPI)
  submit, status, review,     ├─ POST /submissions          ─▶ vetting pipeline ─▶ store
  audit, list, health,        ├─ GET  /submissions/{id}          ├─ validation, rules
  client-check                ├─ POST /submissions/{id}/review   ├─ risk classifier (replay | live)
                              ├─ GET  /submissions/{id}/audit    └─ scanner (Cisco YARA)
agent platform ──HTTP──▶      ├─ GET  /v0.1/servers ─▶ store, or the last-good copy
                              └─ GET  /livez, /readyz
```

| Part | Folder | Job |
| --- | --- | --- |
| API | `api/` | App factory, one router per resource, identity from the bearer token, error mapping to a rule id |
| Vetting | `vetting/` | Validation (step 1), hidden characters (step 2), allowed sources, the decision order as one function |
| Classifier | `risk/` | Versioned prompt, strict answer parsing, replay and live providers, recorder, tiers |
| Scanner | `scanner/` | Adapter over the Cisco MCP Scanner's YARA engine in static mode |
| Store | `store/` | SQLAlchemy on SQLite, append-only audit, the last-good copy |
| Edge | `cli.py`, `cli_input.py`, `cli_output.py`, `client_sim.py` | Typer and Rich CLI over HTTP, client simulator of Amp's documented check |
| Shared | `config.py`, `logging.py`, `models.py`, `interfaces.py`, `fingerprint.py` | Frozen at 14:27 on 17 Nov, before the parallel build |

The pipeline is built once at startup and reused by every request (`tests/api/test_pipeline_wiring.py`).

## Data flow

1. **Submit.** `POST /submissions` with a `server.json` record and its tool list. Identity comes from the bearer token.
2. **Validate.** Pinned schema, pinned version, allowed package source, no remotes, at least one tool. A failure is a 422 with a rule id. It stores an audit event and no decision.
3. **Rules.** Hidden characters in a tool name or description reject the version.
4. **Classify.** Each tool gets a score and capability tags. By default the replay provider answers from `evals/recordings/`, keyed by a hash of prompt version, tool name and description. A miss is never guessed: human review.
5. **Scan.** The YARA engine runs over the tool list. Findings are evidence beside every outcome. A match or a failed scan stops an approval and never rejects alone.
6. **Decide.** The eight steps of the parent spec, first match wins. The decision carries the policy version.
7. **Store.** Decision and audit events in one transaction. Database triggers refuse update and delete on audit, decisions and published records.
8. **Review.** A case in review is decided by a reviewer who is not the submitter, with a note.
9. **Publish and read.** An approval adds an upstream-format record to the published list and rewrites the last-good copy. `GET /v0.1/servers` serves only approved versions, with cursor paging.

What never leaves the service: scores, findings, offending text, reviewer notes and audit records. They are readable through the authenticated submission routes only, never on the registry list.

## Component boundaries

- **Frozen seams** (`interfaces.py`): `Pipeline.vet`, `ClassifierProvider.classify`, `Scanner.scan`, the `Store` protocol, and the signals `Refusal`, `ClassifierUnavailable`, `NoRecording`, `ScannerError`. Injection points are in `api/dependencies.py`: `get_identity`, `get_store`, `get_pipeline`. Fakes for the pipeline, the provider and the scanner are in `tests/fakes.py`.
- **One config module.** Only `config.py` reads the environment (`tests/structure/test_source_rules.py`).
- **One logger.** Every line goes through `log_event` in `logging.py`, which turns untrusted text into a sha256 and a length.
- **Outbound calls.** Two places build an HTTP client, not one wrapper: `cli.py` (`_client`, used by the CLI and the client simulator, towards the registry API) and `risk/live.py` (the model call). Both take an injected transport, which is how the tests stay offline.
- **Area ownership.** `docs/structure.md`. The CLI reaches the service over HTTP only, and nothing under `vetting/`, `risk/` or `scanner/` imports `store/`.

## Trade-offs

Drawn from `docs/spec-notes.md` section 2. Each names what the slice gave up.

- **Rules before the model; the model can escalate and never clear.** Given up: a model that could clear a borderline case on its own. Cost seen in the evaluation: three benign tools in review.
- **Replay as the default provider.** Given up: judging any tool not in the recordings. Every unseen tool goes to a human.
- **Scanner as evidence, own classifier for the decision.** Given up: a single vendor tool for the whole check. The scanner returns no score and no capability tags, so it cannot drive tiers.
- **A last-good copy on the read path.** Given up: freshness while the store is down. The copy has no expiry.

These four are kept as drafted. They come from the spec notes prepared before the build, listed in `agentic-workflow.md`, section 2.

## Security and privacy

- **Untrusted text.** Tool names and descriptions are data, never instructions. The classifier prompt says so and wraps each tool in tags. The recorder is a bare Messages API call with no tools, so a poisoned sample cannot make it act. The CLI prints untrusted text inert: no markup, control and hidden characters escaped (`tests/e2e/test_cli_submit.py::test_untrusted_text_is_printed_inert`). Logs carry hashes, not text.
- **Identity.** From the bearer token only. A review body with an identity field is refused. Stub tokens work only in the `dev` environment.
- **Separation of duties.** On the server: the reviewer's identity is compared with the submitter's, not their roles. An identity without the reviewer role is refused too.
- **What is published.** Upstream `server.json` records of approved versions, nothing else (`tests/contract/test_server_list.py`).
- **Secrets.** One key, only for the recording run, in the shell environment. Full-history secret scan on every pull request and push to `main`. `.dockerignore` keeps `.env` and `.git` out of the image.
- **Supply chain.** `uv.lock`, with `--locked` in every stage of the check script. CI actions pinned to a commit. Two `litellm` advisories waived, with a record in `decisions.md`.

## Controls on the coding agent: advisory and enforced

From `.claude/settings.json`, `.claude/hooks/`, `CLAUDE.md` and the repository settings, as in force during the build.

| Question | Advisory | Enforced |
| --- | --- | --- |
| What to do | `CLAUDE.md`, the spec and one child per session, a brief per session, skills (`tdd-behaviour`, `verify-change`, `handoff`) | Plan mode at the start of each session: no edit before the user approves the plan. The `SessionStart` hook prints the brief and the handoff note |
| What it can touch | Folder ownership in `docs/structure.md` and the briefs. One git worktree per area session | Deny rules: reading `.env` and `secrets/`, editing `evals/recordings/`, amend, rebase, reset, force push, `gh pr merge`. Ask rules: push, merge, `gh pr create`, `uv add`, `make record`. From 14:19, auto mode's safety check, which blocked one command. Structure tests: only `config.py` reads the environment, 350-line limit. The test network guard |
| When it is done | `verify-change` skill: paste real output before claiming done | `Stop` hook runs `verify.sh quick` and `test` at the end of each turn. It lets a second stop through with a warning. CI on every pull request |
| How much it spends | Time budgets in the briefs | Nothing in the repo |
| Who has the last word | Reviewer subagent reports. The agent proposes a decision per finding | The user decides each review finding, opens and merges every pull request and starts the recording run. Checks are not marked required, so merging on green is the user's discipline |

## Technology choices

The stack was fixed by the spec before the build.

- **Python 3.12, uv.** One lockfile, `uv run --locked` in the check script, `uv audit` in CI.
- **FastAPI, uvicorn, Pydantic v2, pydantic-settings.** Typed request models, dependency overrides as the test seam, one validated settings object.
- **SQLAlchemy 2 on SQLite.** No server to run. Triggers make audit append-only.
- **Typer and Rich.** Commands that never prompt, `--help` with examples, styled but inert output.
- **httpx.** The live provider speaks the Anthropic Messages API with no SDK, and both clients take a mock transport in tests.
- **jsonschema.** Submissions are checked against the pinned upstream `server.json` schema 2025-12-11; the list against the pinned OpenAPI 2025-12-01.
- **Scanner, buy versus build.** Bought: the YARA engine of `cisco-ai-mcp-scanner` 4.8.7 (Apache 2.0), pinned, static mode, offline, no key. Built: the classifier, because the scanner returns no score and no capability tags. Fit test at 14:38: the benign sample was clean and `poisoned-notes` got two HIGH findings. Cost: importing it made LiteLLM try the network until `config.py` set `LITELLM_LOCAL_MODEL_COST_MAP` (`4dd0c9a`), and it brought two waived advisories. Result in the evaluation: 6 of 16 malicious cases matched, none of them changed an outcome.

## Production shape

In words only, from `docs/spec-notes.md` section 3, `deploy/README.md` and `ROADMAP.md` Phase 2. The deployment route is in [`operate.md`](operate.md).

- Single sign-on replaces the stub tokens; reviewer is a directory group.
- Managed PostgreSQL with migrations; audit insert-only by grants as well as triggers; audit streamed to the SIEM.
- The read path served separately, read-only and cacheable; the last-good copy in object storage, with a maximum age and an alert.
- Live classifier on an in-region endpoint, behind an egress allowlist, with the evaluation gate rerun on every change of model, prompt or threshold.
- Packages pointed at the internal artifact repository, with a package digest in the submission so that an approval binds to the bytes.
- A way to withdraw an approved version, and an export of the approved set as a managed-settings allowlist for clients that do not read a registry.
