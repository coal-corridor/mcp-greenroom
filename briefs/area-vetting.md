# Brief: vetting area

Session: its own worktree, branch `area/vetting`. Starts when the contracts are frozen. One pull request.

## Goal

Given a submission, the pipeline returns the outcome the spec's decision order demands, with evidence, for every sample and every evaluation case.

## Owns

`src/mcp_greenroom/vetting/`, `src/mcp_greenroom/risk/`, `src/mcp_greenroom/scanner/`, `evals/`, `tests/unit/`. Nothing else. Shared modules and `contracts/` are frozen.

## Read first

`docs/specs/mcp-greenroom.md` (the parent: decision order, invariants, shared criteria), then `docs/specs/vetting.md` in full. No other child spec. From `docs/references.md`, at most the Cisco scanner's static mode.

## Deliver

1. Validation and the deterministic rules: schema, pinned version, allowed source, tool count, hidden characters. Each refusal carries a stable rule id and a three-part message.
2. The fingerprint over manifest and tool definitions.
3. The decision order, exactly as numbered in the spec, as code that is easy to read against it.
4. Classifier providers behind the interface: replay (default) and live. The prompt is a versioned file. It tells the model to treat the description as data and to answer in JSON only. For the live provider and the recorder, use the `claude-api` skill if the profile has it, to get the current request shape and model names right. Keep to httpx: no SDK.
5. Scanner rules through the package's static mode, behind the scanner interface. Its output is untrusted text.
6. `evals/`: about 40 labelled synthetic tool descriptions as the spec lists them, thresholds, and the evaluation run with its gate and report, including the scanner column.
7. `make record`, used only through `/record-classifier`. It writes to `evals/recordings/`, which the edit tools are denied: the recorder is the only writer.

## Tests to write first

One test per rule. One test per step of the decision order, in order. "Provider failure never approves." "A scanner match never approves and never rejects alone." The fingerprint under reordering. The table of sample outcomes.

## Done when

`./scripts/verify.sh` passes in this worktree, the evaluation gate passes on real recordings, and the report is saved for `evidence/verify.md`.

## Cut first

The scanner rules, then the live provider's configurable endpoint beyond what the recording run needs.

## Stop and ask

A sample does not land where the table says. The gate fails after recording. The scanner flags the benign sample. Anything that would make a test call the network.
