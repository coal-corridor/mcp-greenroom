---
name: write-evidence
description: Write or update the README and the evidence pack from real output. Use for README.md and for any file under evidence/.
paths:
  - "README.md"
  - "evidence/**"
---
# Write evidence from real output

Every number, result and quoted output in these files comes from a command run in this session. Run it, then paste it. If something was not run or not built, say so in the file. Never describe a feature that was cut.

One page per evidence file. What each one holds:

| File | Holds |
| --- | --- |
| `README.md` | What the solution does, prerequisites, setup, run command, check command, one example workflow, known limits, where the evidence is |
| `evidence/intent.md` | Problem, users, assumptions, constraints, out of scope, success criteria |
| `evidence/design.md` | Architecture, data flow, component boundaries, trade-offs, security and privacy, technology choices, production shape |
| `evidence/agentic-workflow.md` | Tools, decomposition, prompts as sent, interventions, review findings, timeline, what was prepared in advance |
| `evidence/verify.md` | Check script table, evaluation table, demo output, dependency audit result, link to the CI run, known gaps, local versus pipeline checks |
| `evidence/operate.md` | How to run, logs and status, config and secrets, failure modes (symptom, effect, action), rollback and degrade, local to cloud |
| `evidence/decisions.md` | Three to five records: context, decision, consequences, and what was not built on purpose |

Background for `design.md`, `decisions.md` and `operate.md` is in `docs/spec-notes.md` and `docs/references.md`. Use it, and keep its "unverified" marks.

Writing rules:

- Plain words, short sentences, for a senior engineer. No filler.
- No em dashes and no en dashes. Use commas, colons, brackets or a new sentence.
- Name each known gap and the production route that closes it.
- Do not fill in a `TODO(build)` marker with a guess. Ask the user for anything only they know.
