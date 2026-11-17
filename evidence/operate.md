# Operations: MCP Greenroom

Written from the running service on 17 Nov 2026, at commit `f117754`. Nothing here was deployed: the slice runs on one machine.

## Run

From a fresh clone, as tested in [`verify.md`](verify.md):

```sh
uv sync                # once per clone
make run               # the API on http://127.0.0.1:8000
./scripts/demo.sh      # or: start its own service on port 8765, walk the demo, stop it
```

`make run` is `uv run uvicorn mcp_greenroom.api.main:app --host 127.0.0.1 --port 8000`. It needs no key and no network: the classifier replays recordings and the scanner runs offline. Data goes to `./mcp-greenroom.db` and `snapshots/last-good.json` unless configured.

Container: `docker compose up --build`, then `uv run mcp-greenroom health --api http://127.0.0.1:8000`. Built and run once from the fresh clone (Docker 29.7.2):

```text
build exit 0
✓ live
✓ ready
✓ registry normal
Next: mcp-greenroom list
health exit 0
```

The compose file binds `127.0.0.1:8000` only and keeps the database and the last-good copy in a named volume at `/data`.

## Logs and status

One JSON line per request and per decision, on standard error, through `log_event`. Tool names and descriptions never appear in a log line, only their hashes (`tests/api/test_operability.py::test_logs_carry_no_tool_text`). From `make run`'s app, with a temporary database:

```text
{"duration_ms": 12.954, "event": "http.request", "level": "INFO", "method": "POST", "path": "/submissions", "status": 201, "ts": "2026-11-17T05:10:46.738586+00:00"}
{"decided_by": "policy", "event": "decision", "level": "INFO", "outcome": "approved", "policy_version": "2026-11-17.1", "reason_codes": ["policy.tier_low"], "submission_id": "39422963-1917-41bb-9e62-074ec0d585d7", "tier": "low", "ts": "2026-11-17T05:10:46.738001+00:00"}
```

Liveness and readiness, normal and then with the database file replaced by junk:

```text
$ curl -s -i /livez
HTTP/1.1 200 OK
{"alive":true}

$ curl -s /readyz
{"ready":true,"snapshot_generated_at":"2026-11-17T05:10:46.318869+00:00"} -> 200

--- store broken
$ curl -s /readyz
{"ready":false,"reason":"store unavailable: database error: DatabaseError"} -> 503

$ curl -s -D- /v0.1/servers
HTTP/1.1 200 OK
x-greenroom-degraded: true
x-greenroom-generated-at: 2026-11-17T05:10:46.736370+00:00
{"servers":[{"server":{... "name":"com.examplebank/payments-readonly", ... "version":"1.2.0"}, ...}],"metadata":{"count":1}}
```

The log line for the degraded read: `{"error": "database error: DatabaseError", "event": "list.degraded", "generated_at": "2026-11-17T05:10:46.736370+00:00", "level": "INFO", ...}`. `mcp-greenroom health` prints the same three facts, one line each, and exits 1 when not ready.

## Configuration and secrets

All settings are read in one module, `src/mcp_greenroom/config.py`, with the prefix `MCP_GREENROOM_`, from the environment or a local `.env`. Every one has a safe default, so the slice runs with none set.

| Variable | Default | Notes |
| --- | --- | --- |
| `ENV` | `dev` | The only accepted value. Stub tokens work only here |
| `API`, `TOKEN` | `http://localhost:8000`, none | Read by the CLI only |
| `DATABASE_URL` | `sqlite:///./mcp-greenroom.db` | |
| `SNAPSHOT_PATH` | `snapshots/last-good.json` | The last-good copy |
| `RISK_PROVIDER` | `replay` | `live` needs `MODEL` and `MODEL_API_KEY` |
| `RECORDINGS_DIR` | `evals/recordings` | |
| `MODEL_BASE_URL`, `MODEL`, `MODEL_API_KEY` | `https://api.anthropic.com`, empty, none | Live provider only |
| `REJECT_THRESHOLD`, `APPROVE_THRESHOLD` | `0.80`, `0.20` | Approve must stay below reject |
| `REQUIRE_HUMAN_FOR_ALL` | `false` | Sends every low-tier case to review |
| `POLICY_VERSION` | `2026-11-17.1` | Must change when a threshold or the flag above changes |
| `LOG_LEVEL` | `INFO` | |

A bad value stops startup with one message: what failed, what was received, what to do. From the break test:

```text
Invalid configuration: MCP_GREENROOM_REJECT_THRESHOLD changed the policy, but MCP_GREENROOM_POLICY_VERSION is still 2026-11-17.1. Set a new MCP_GREENROOM_POLICY_VERSION, so each decision names the policy that made it. Fix the variable in the environment or in .env (see .env.example), then start again.
make: *** [Makefile:8: run] Error 1
```

The one key, `MCP_GREENROOM_MODEL_API_KEY`, is needed only for the recording run (`make record`, started by the user). It lives in the shell environment, never in a file in the repo. It is held as a secret type and printed as `<hidden>` in a config error. The full-history secret scan finds no leak (`verify.md`). The agent harness denies reading `.env` and `secrets/`. Those rules match tool calls, not intent: a deny on `Read(./.env)` does not stop a shell command that prints the same file, and an agent's shell inherits the environment of the shell that started it.

## Failure modes

| Symptom | Effect | Action | Shown by |
| --- | --- | --- | --- |
| Startup prints `Invalid configuration: ...` and exits | Service does not start | Fix the named variable, start again | Break test, section 1 |
| `/readyz` 503 `store unavailable`, `list` warns `degraded` | List served from the last-good copy. Submit, status and review refused with 503 `store.unavailable` | Restore the database, restart | Demo safe failure 5; break test 3b; `tests/failure/test_degrade.py` |
| Store down at startup and no last-good copy | `list` 503: "no last-good copy yet to serve". Submit 503 | Restore the database, restart | Break test 3a |
| `/readyz` 503 naming the last-good copy | Publish stands, but the copy on disk is stale | Fix the snapshot path or disk, then publish again | `tests/failure/test_snapshot_failure.py` |
| Decision `human_review` with `classifier.no_recording` or the classifier unavailable | Nothing approved; a reviewer decides | Review it, or record the tool | Demo safe failure 3; `tests/unit/test_decision_order.py` |
| Decision `human_review` after a scanner failure | Nothing approved | Review it; check the log for `ScannerError` | `tests/unit/test_decision_order.py::test_step_6_a_scanner_that_fails_sends_to_human_review` |
| HTTP 500 from submit | Nothing stored; error logged with a hash, no trace in the body | Read the log line, fix, resubmit | `tests/failure/test_pipeline_crash.py` |
| `client-check` blocks every server | The client simulator could not read the list | Check the registry is reachable | `tests/e2e/test_client_sim.py` |

## Rollback and degrade

- **Last-good copy.** On every publish the service writes the approved list to `SNAPSHOT_PATH` in one atomic step. When the database fails, `GET /v0.1/servers` serves that copy, with `X-Greenroom-Degraded: true` and `X-Greenroom-Generated-At`. The body stays in upstream format, so a client that reads only the body cannot tell.
- **Refused while degraded.** Submit, status and review answer 503 `store.unavailable`. Nothing can be approved while the store is down.
- **Staleness.** The copy has no expiry. Its age shows in the header, on `/readyz` and in `mcp-greenroom list`. Route: a maximum age and an alert (ROADMAP Phase 2, item 13).
- **Recovery.** Restore the database and restart. A schema setup that failed at startup is not retried, so a restart is needed even after the database comes back. An empty database at startup overwrites the last-good copy with an empty list. Both are deferred (registry review 7, ROADMAP).
- **Rollback of a decision.** None. An approved version cannot be withdrawn in the slice (ROADMAP Phase 2, item 6). The audit trail is append-only, enforced by database triggers.

## Local to cloud

In words only. None of this was built. Sources: `docs/spec-notes.md` section 3, `deploy/README.md`, `ROADMAP.md` Phase 2 item 11.

- **Build.** One image from `uv.lock`, as `Dockerfile` does today, scanned before it is pushed.
- **Verify.** The same `./scripts/verify.sh` is the gate at every step: on the laptop, on each pull request, and before each promotion. The evaluation gate reruns on every change of model, prompt or threshold.
- **Promote.** Through environments, each gated by the same script, with a required second reviewer on the pull request.
- **Shape.** The write path (submit, review, audit) stays internal behind single sign-on. The read path (`GET /v0.1/servers`) is a read-only, cacheable service or a signed static copy at the edge. A managed database replaces SQLite, object storage holds the last-good copy, and logs go to the central log store.
- **Agents in the pipeline.** A hosted agent review posts findings on the pull request and never approves or merges. Headless agent runs are judged by their exit code and a JSON result, never by their prose. The harness (`CLAUDE.md`, settings, hooks, skills, the reviewer) is shared as one versioned plugin, so every repository gets the same guard rails.
