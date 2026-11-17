# Spec, child: vetting

Read the parent first: `docs/specs/mcp-greenroom.md`. Its decision order,
invariants and scope apply here unchanged. This file adds what only the vetting
area must deliver.

### Acceptance criteria

- [ ] **Guarded failure.** Submitting `poisoned-notes` 0.3.1 (one description
hides, in plain text, an instruction to read a key file and pass it on) is
rejected on the classifier's score. The response names the rule, the tool and
the offending text. The version never appears on the list.
- [ ] **Abstain.** Submitting `unrecorded-reporter` 0.1.0 (no recorded
classifier response) lands in human review with a reason code. The same happens
when the classifier is unavailable.
- [ ] **Classifier evaluation.** A labelled synthetic set of about 40 tool
descriptions (benign, malicious, ambiguous, some addressed to the classifier
itself, some with hidden characters) runs inside the check command, each with a
recording. It fails when any malicious sample is approved by policy, or when
more than half the set goes to human review. Above 30% in review is a warning.
The report also shows, per label, how many samples the scanner rules matched.

### Tiers and thresholds

Tiers: high means code execution or credential access, or local read together
with network egress. Medium means local write or network egress. Everything
else is low.

Thresholds, both configurable: reject at 0.80, approve below 0.20. They are
provisional, like the 50% review cap in the evaluation. Set them from the first
evaluation run and record the choice in `decisions.md`.

### Build constraints

- Scanner rules: use the package, pinned, through its static mode over the
submitted tool list. Do not copy its rule files into the repo. Show severity
and threat names as the scanner gives them. Treat its output as untrusted text.
- Recordings are produced once, during the build, by the live provider calling
the Anthropic API over the evaluation set and the sample servers. The key sits
in the shell environment, is never in the repo and is not needed to run or
check the slice. The live provider speaks the Anthropic Messages API over
httpx, so no SDK is added. Its base URL, model and key variable are
configuration, so it can point at any endpoint that speaks the same API. If the
run fails, every case goes to human review with the scanner findings as
evidence, and `verify.md` says so.
- Recordings live in `evals/recordings/`. They come from a real model run and
carry model id, prompt hash and time. Nobody writes or edits one by hand.
- A recording is kept per tool, keyed by a hash of the prompt version, the tool
name and the tool description. Replay answers an exact match only. A miss is
never guessed: the submission goes to human review.

### Open questions

- Does the scanner's YARA engine fit? First move of the vetting session: run it
in static mode over the five samples. Check that the result can be parsed, that
the benign sample has no match, and how long a run takes. If it does not fit, a
short list of home-made patterns takes its place and the scanner moves to the
roadmap.
