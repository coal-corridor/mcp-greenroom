# Sample servers

Five synthetic server versions under `com.examplebank`, one per named criterion. Each file is a submission body: `server` (a `server.json`, validated against `contracts/server.schema.json`) and `tools` (the tool definitions that `server.json` does not carry). No real data. `poisoned-notes` holds a hostile description on purpose: it is test data, never an instruction.

| File | Version | Expected outcome | Why | Criterion |
| --- | --- | --- | --- | --- |
| `payments-readonly.json` | 1.2.0 | approved by policy, tier low, under 5 s | Benign, read-only tools | Main path (parent) |
| `invalid-unpinned.json` | `latest` | refused, 422, stable rule id, nothing stored | Version not pinned, at both levels. The pinned schema refuses `latest` on `packages[].version` but accepts it on the top-level `version`, so vetting needs its own rule for the latter | Validation rejection (parent) |
| `poisoned-notes.json` | 0.3.1 | rejected on the classifier's score; response names rule, tool (`search_notes`) and offending text | A plain-text instruction to read a key file and pass it to another tool | Guarded failure (vetting) |
| `unrecorded-reporter.json` | 0.1.0 | human review, with a reason code | No classifier recording exists for its tool. The recording run must skip this sample | Abstain (vetting) |
| `ambiguous-exporter.json` | 2.0.0 | human review, tier medium (low score) | Sends a report to a caller-chosen URL: network egress | Separation of duties (registry) |

Reason codes and rule ids are vetting's to name. This table fixes outcomes only.
