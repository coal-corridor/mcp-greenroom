# Operations: MCP Greenroom

Status: headings only, prepared before the timed build. Written from the running service. One page.

## Run

`TODO(build)`: the commands, as tested from a fresh clone.

## Logs and status

`TODO(build)`: one real log line for a request and one for a decision. The liveness and readiness endpoints with real responses, normal and degraded.

## Configuration and secrets

`TODO(build)`: the variables, their defaults, and what happens on a bad value. Where the one key lives and where it never appears. Note that permission rules in the agent harness match tool calls, not intent.

## Failure modes

`TODO(build)`: from behaviour that was actually exercised.

| Symptom | Effect | Action |
| --- | --- | --- |
| | | |

## Rollback and degrade

`TODO(build)`: the last-good copy, what is refused in degraded mode, how to recover, and how stale the list may get.

## Known gaps

- Scanner thread safety: not verified. One scanner instance (the Cisco MCP Scanner's `StaticAnalyzer`) is built at startup and shared by every request thread. Whether the package is safe to share was not checked. The adapter holds a lock, so one scan runs at a time (`src/mcp_greenroom/scanner/yara.py`, test `tests/unit/test_scanner_lock.py`). Effect: concurrent submissions queue on the scan. Production route: confirm the package's thread safety, then drop the lock or keep a small pool of scanners.

## Local to cloud

`TODO(build)`: how the slice would be built, verified and promoted. The same check script as the gate at each step. From `docs/spec-notes.md`, section 3. Agents in the pipeline, in words only: a hosted review that posts findings and never approves, headless runs checked by exit code and JSON result, the harness shared as one versioned plugin.
