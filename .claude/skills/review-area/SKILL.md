---
name: review-area
description: Independent review of the current branch against the spec, by a read-only reviewer with a fresh context. Run before opening a pull request.
disable-model-invocation: true
context: fork
agent: reviewer
background: false
allowed-tools: Bash(git diff *)
---
Review the change below against the spec. You did not write it. Read `docs/specs/mcp-greenroom.md` (the parent), then only the child specs in `docs/specs/` whose area owns the changed files: `docs/structure.md` maps folders to areas. On the integration branch that can be all three area children. Skip `stretch.md` unless the diff builds a stretch item.

Changed files:

!`git diff --stat main...HEAD`

Diff:

!`git diff main...HEAD`

Answer pass or fail for each point, with file and line:

1. Every acceptance criterion this change claims has a test that asserts the behaviour.
2. No path approves a version when a rule or the scanner has stopped it, or when the classifier failed, was missing or was uncertain.
3. Separation of duties is enforced on the server, from the caller's credential.
4. Error responses carry a rule id and no stack trace. Untrusted text is never logged, and never printed raw.
5. Tests and the check script make no network call. No secret or key is in the diff.
6. Every decision writes an audit record with the policy version. Audit records have no update or delete.
7. Nothing in the diff is outside the scope of the spec.
8. No test was weakened: no removed assertion, no new skip or xfail marker, no loosened expected value without a stated reason.

Report only gaps that affect correctness or safety. Skip style. Finish with a table, most severe first: finding, severity, file and line, suggested fix. If you find nothing, say so and list what you checked.
