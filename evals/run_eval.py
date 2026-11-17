"""Run the evaluation: every case and the named samples through the default pipeline, then
the gate. Exit 0 when the gate passes, 1 when it fails.

    uv run python -m evals.run_eval [--out report.md]
"""

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from evals.cases import UNRECORDED, case_submission, load_dataset, load_sample
from evals.gate import MAX_REVIEW_SHARE, WARN_REVIEW_SHARE, CaseResult, judge, label_table
from mcp_greenroom.config import Settings, load_settings
from mcp_greenroom.interfaces import Refusal
from mcp_greenroom.models import Decision, FindingSource, Outcome, Tier
from mcp_greenroom.vetting.factory import build_pipeline
from mcp_greenroom.vetting.pipeline import VettingPipeline


@dataclass(frozen=True)
class Expected:
    outcome: str  # an Outcome value, or "refused"
    tier: Tier | None = None
    code: str | None = None
    tool: str | None = None


# The table of sample-data/servers/README.md. Reason codes are vetting's to name.
SAMPLES: dict[str, Expected] = {
    "payments-readonly": Expected(Outcome.APPROVED.value, Tier.LOW, "policy.tier_low"),
    "invalid-unpinned": Expected("refused", code="validation.version_not_pinned"),
    "poisoned-notes": Expected(
        Outcome.REJECTED.value, code="classifier.reject_threshold", tool="search_notes"
    ),
    UNRECORDED: Expected(Outcome.HUMAN_REVIEW.value, code="classifier.no_recording"),
    # Outcome and tier only: sample-data/servers/README.md says the table fixes outcomes, and
    # reason codes are vetting's to name. The sample may reach review at step 5 (uncertain
    # score) before step 7 (tier medium); both are human review at tier medium (user decision).
    "ambiguous-exporter": Expected(Outcome.HUMAN_REVIEW.value, Tier.MEDIUM),
}


def _codes(decision: Decision) -> tuple[str, ...]:
    return tuple(r.code for r in decision.reasons)


def _scanner_matched(decision: Decision) -> bool:
    return any(f.source is FindingSource.SCANNER for f in decision.findings)


CAPABILITIES: dict[str, str] = {}  # case id -> capability tags the classifier returned


def run_cases(pipeline: VettingPipeline) -> list[CaseResult]:
    results = []
    for case in load_dataset():
        decision = pipeline.vet(case_submission(case))
        tags = sorted({c.value for r in decision.risks for c in r.capabilities})
        CAPABILITIES[case.case_id] = ", ".join(tags) or "-"
        results.append(
            CaseResult(
                case.case_id,
                case.label,
                decision.outcome,
                _codes(decision),
                _scanner_matched(decision),
            )
        )
    return results


def run_samples(pipeline: VettingPipeline) -> tuple[list[list[str]], list[str]]:
    """Rows for the report, and one failure per sample that misses its expected outcome."""
    rows: list[list[str]] = []
    failures: list[str] = []
    for slug, expected in SAMPLES.items():
        started = time.perf_counter()
        try:
            decision = pipeline.vet(load_sample(slug))
            got, tier = decision.outcome.value, decision.tier
            codes, tools = _codes(decision), {r.tool_name for r in decision.reasons}
        except Refusal as refusal:
            got, tier, codes, tools = "refused", None, (refusal.rule_id,), set()
        elapsed_ms = (time.perf_counter() - started) * 1000
        ok = (
            got == expected.outcome
            and (expected.tier is None or tier is expected.tier)
            and (expected.code is None or expected.code in codes)
            and (expected.tool is None or expected.tool in tools)
        )
        if not ok:
            failures.append(
                f"sample {slug} landed on {got} (tier {tier.value if tier else '-'}, "
                f"reasons {', '.join(codes)}), expected {expected.outcome}"
                f"{f' tier {expected.tier.value}' if expected.tier else ''}"
                f"{f' reason {expected.code}' if expected.code else ''}"
                f"{f' on tool {expected.tool}' if expected.tool else ''}"
            )
        tier_text = tier.value if tier else "-"
        rows.append(
            [slug, got, tier_text, ", ".join(codes), f"{elapsed_ms:.0f}", "yes" if ok else "NO"]
        )
    return rows, failures


def _table(header: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + " --- |" * len(header)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return lines


def report(results: list[CaseResult], sample_rows: list[list[str]], policy: str) -> list[str]:
    columns = ["label", "total", "approved", "human_review", "rejected", "scanner_matched"]
    by_label = [[str(row[c]) for c in columns] for row in label_table(results)]
    cases = [
        [r.case_id, r.label, r.outcome.value, ", ".join(r.codes), CAPABILITIES.get(r.case_id, "-")]
        for r in results
    ]
    return [
        f"# Classifier evaluation (policy {policy})",
        "",
        "## By label",
        "",
        *_table(columns, by_label),
        "",
        "## Named samples",
        "",
        *_table(["sample", "outcome", "tier", "reasons", "ms", "as expected"], sample_rows),
        "",
        "## Cases",
        "",
        *_table(["case", "label", "outcome", "reasons", "capabilities"], cases),
    ]


def eval_settings() -> Settings:
    """Settings for the gate: always replay, always the default policy. The shell may hold
    the recording run's live settings; the check command must never call the network."""
    settings = load_settings()
    fields = Settings.model_fields
    return settings.model_copy(
        update={
            "risk_provider": "replay",
            "model_api_key": None,
            "reject_threshold": fields["reject_threshold"].default,
            "approve_threshold": fields["approve_threshold"].default,
            "require_human_for_all": fields["require_human_for_all"].default,
            "policy_version": fields["policy_version"].default,
        }
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the classifier evaluation and its gate.")
    parser.add_argument("--out", type=Path, help="also write the report as Markdown here")
    args = parser.parse_args(argv)

    settings = eval_settings()
    pipeline = build_pipeline(settings)
    results = run_cases(pipeline)
    sample_rows, sample_failures = run_samples(pipeline)
    verdict = judge(results)

    lines = report(results, sample_rows, settings.policy_version)
    failures = [*verdict.failures, *sample_failures]
    lines += ["", "## Gate", ""]
    lines += [
        f"Thresholds: reject at {settings.reject_threshold:.2f}, approve below "
        f"{settings.approve_threshold:.2f}. Review cap {MAX_REVIEW_SHARE:.0%}, "
        f"warning above {WARN_REVIEW_SHARE:.0%}. In review: {verdict.review_share:.0%}.",
        "",
    ]
    lines += [f"- FAIL: {f}" for f in failures]
    lines += [f"- WARNING: {w}" for w in verdict.warnings]
    lines += ["- PASS" if not failures else ""]
    text = "\n".join(lines).rstrip() + "\n"
    sys.stdout.write(text)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    if failures:
        sys.stderr.write(
            "Evaluation gate failed: see the FAIL lines above. Change a sample's wording, "
            "never a recording; only the user changes a threshold.\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
