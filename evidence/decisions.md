# Decisions: MCP Greenroom

Format of a record: context, decision, consequences. The context and the consequences are facts from the build, with their trace. The user writes the trade-offs in their own words, and each record marks where it quotes them.

## Waive two litellm advisories in the dependency audit

Context: on 2026-11-17, `uv audit` (uv 0.13.8) on the first lock found two advisories in `litellm 1.93.2`: GHSA-g5ff-637f-6q2m (local file read, fixed in 1.95.0) and GHSA-7hp6-4w63-5g45 (privilege escalation to proxy admin, fixed in 1.100.4 and later). `litellm` comes only through `cisco-ai-mcp-scanner` 4.8.7, which pins it exactly (`litellm==1.93.2`), so a bump would override the scanner's own pin. Both advisories are in the LiteLLM proxy server. This project uses only the scanner's YARA engine and never starts that proxy.

Decision (the user's): keep the scanner and waive both IDs under `[tool.uv.audit]` in `pyproject.toml`. After the waiver, `uv audit` reports no known vulnerabilities in 118 packages, exit 0. Not chosen: dropping the scanner, overriding `litellm`, or leaving both advisories open.

Consequences: the vulnerable code still ships in the environment, unused. The waiver hides these two IDs only, and any new advisory still shows. The audit job stays in CI. Production route: remove the waiver once a scanner release unpins `litellm` at a fixed version, or vendor only the YARA rules and drop the package.

## Secret scan with the pinned gitleaks binary, not the action

Context: `docs/specs/delivery.md` asked for a secret scan over the full history, using the official gitleaks action. On 2026-11-17 the source of `gitleaks/gitleaks-action` v3.0.0 (commit `e0c47f4`, `src/index.js`) showed how it picks the range: on `push` it scans from the first to the last commit of the push, and on `pull_request` it scans the pull request's commits. A full-history scan happens only on `workflow_dispatch` and `schedule`. Research stopped there at the user's request.

Decision (the user's): the `secret scan` job downloads the gitleaks 8.30.1 release tarball, checks its sha256 (`551f6fc8...`, from the release's checksums file), and runs `gitleaks git --redact --verbose --exit-code 1 .` over a checkout with `fetch-depth: 0`. `delivery.md` now names the binary instead of the action.

Consequences: every pull request and every push to `main` scans the full history. No licence key and no token are needed, and the job keeps read-only permissions. A gitleaks upgrade means changing the version and the sha256 by hand. The first run on PR #1 (run 44008340480) passed in 8s. Because the scan covers the full history, a false positive in an old commit cannot be fixed by a new one: see the next record.

## Allow the replay keys of the classifier recordings in the secret scan

Context: on pull request 4, run 44018534676 (head `4b32a1e`), the secret scan reported 47 findings of the `generic-api-key` rule, one on line 5 of each recording committed in `827782a`, field `"key"`. Each value is the replay key: a SHA-256 hex digest of prompt version, tool name and description, equal to the file name. The API key was only ever sent in a request header and is in no recording. History is never rewritten, so the findings stay in the scanned range.

Decision (the user's): `.gitleaks.toml` (`eedd2ca`) keeps the default rules and adds one allowlist: rule `generic-api-key` only, condition AND of path `^evals/recordings/[^/]+\.json$` and secret `^[0-9a-f]{64}$`.

Consequences: run 44018904544 (head `cc5760a`) passed. Any other secret in a recording, or a 64-hex value anywhere else, is still reported. The allowlist was not tested locally first: the auto mode safety check blocked a command that wrote the file and downloaded gitleaks in one step, and the CI run over the full history was the test.

## Switch the sessions to auto mode

Context: the lead session ran in plan mode, then accept edits from 13:48. At 14:05 setup was at 27 minutes against a budget of 10 (`session-log.md`).

Decision (the user's), at 14:19: auto mode for the lead session, and for each area session from plan approval. Reason recorded in the session log: most of the lost time went on approval prompts, and the deny and ask rules still hold.

Consequences: the deny and ask rules stayed in force (`.claude/settings.json`). The session log records one command blocked by the auto mode safety check (15:39, above). In the user's words: auto mode saved the build. Before the switch, about twenty approval prompts and one research detour made setup take 30 minutes against a budget of 10. After it, the three area sessions ran 10 to 18 minutes each without a question. The cost was that I no longer saw each command, so I relied on the deny and ask rules, the independent reviews and CI to catch what I would have caught by watching.

## Record the classifier with Haiku after Opus refused hostile input

Context: the recordings come from one live run over the evaluation set and the sample tools (`docs/specs/vetting.md`). Run 1 on `claude-opus-5-5` (`827782a`) refused 17 of 47 tools: all 16 malicious cases and `search_notes` in `poisoned-notes`. Each refusal went to human review, none was approved, and the gate failed because `poisoned-notes` landed in review instead of rejected. By label (approved, review, rejected): benign 17/1/0, malicious 0/12/4, ambiguous 0/6/1.

Decision (the user's): run 2 on `claude-haiku-5-5` (`66567b5`), same prompt `classifier-v1`. In the user's words: I chose Haiku for the second run because Opus refused 17 of the 47 inputs, Haiku was the model I had already verified with the key, and the re-run needed no code change. I kept the Opus run in history as the record of the refusals.

Consequences: no refusals. Benign 15/3/0, malicious 0/0/16, ambiguous 0/7/0; `poisoned-notes` rejected at 0.97. The gate then failed on the reasons given for `ambiguous-exporter`, and the user had that sample checked on outcome and tier only (`d609a19`). Two benign tools were tagged `network_egress` and go to review. The evaluation now proves behaviour for this model and prompt only.

## Keep the thresholds at 0.80 and 0.20

Context: `docs/specs/vetting.md` calls both thresholds provisional and asks for them to be set from the first evaluation run, with the choice recorded here. With the Haiku recordings and the defaults (reject at 0.80, approve below 0.20), the evaluation puts 24% of cases in review against a cap of 50% and a warning above 30%, and approves no malicious case.

Decision (the user's): no threshold was moved (`session-log.md`, 15:16). In the user's words: I kept the spec's provisional 0.80 and 0.20 because the first full run gave 24% in review with no malicious case approved, and I would not move a safety threshold to make one sample check pass.

Consequences: startup refuses a threshold or require-human change while the policy version is still the default (`d4516d1`). Two non-default policies can still share one version string; the route is in `ROADMAP.md`.

## What was not built on purpose

- **No stretch item.** Tracing, submission by upstream reference, the interactive menu, the per-version endpoints and the shadowing rule were not built. When the evidence pass began, the integration reviews were still running, so the brief's condition ("only if all of the above is green") had not been reached.
- **Nothing from the cut order was cut.** The scanner rules, container files, CLI commands and the type check stage are all in. The scanner adapter was green at 15:19, inside its 15:30 cap.
- **The spinner** (edge, cut first) was not built.
- **Deferred from the area reviews**, each with a recorded decision: duplicate tool names, a complete answer to registry-override arguments, allowed sources as a setting, version-aware client matching, parsing `docker run`, the degraded flag in `list --json`, and seven more. All are listed in `ROADMAP.md`.
- **Out of scope by the spec**: sandbox introspection, runtime inspection, single sign-on, a reviewer screen, a production database, withdrawal of an approved version, any deployment.

## What I read line by line

Most of it, during the build. Merges relied on green checks, the independent reviewer reports and my decision on each finding.

## Harness choices

Included, as in force during the build: `CLAUDE.md` and `AGENTS.md`; `.claude/settings.json` with allow, deny and ask rules; three hooks (`SessionStart` prints the brief and handoff note, `Stop` runs lint, types and tests, a format hook on write); seven project skills; one read-only reviewer subagent; one git worktree per area session; briefs and handoff notes as the only state passed between sessions.

Left out, in the user's words: no Claude in CI, so the pipeline needs no repository secret and its result does not depend on a model. No plugins or connectors, so the profile is reproducible and nothing runs with my privileges unreviewed. No practice pass and no `/code-review`, both for time.
