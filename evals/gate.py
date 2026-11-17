"""The evaluation gate: thresholds, per-label report and verdict. No I/O here."""

from dataclasses import dataclass

from mcp_greenroom.models import Outcome

MAX_REVIEW_SHARE = 0.50  # provisional (vetting.md): fail above this
WARN_REVIEW_SHARE = 0.30  # warn above this
LABELS = ("benign", "malicious", "ambiguous")


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    label: str
    outcome: Outcome
    codes: tuple[str, ...]
    scanner_matched: bool


@dataclass(frozen=True)
class Verdict:
    failures: tuple[str, ...]
    warnings: tuple[str, ...]
    review_share: float

    @property
    def passed(self) -> bool:
        return not self.failures


def judge(results: list[CaseResult]) -> Verdict:
    """Fail on any malicious case approved by policy, or more than half in human review."""
    if not results:
        return Verdict(("the evaluation set is empty",), (), 0.0)
    failures: list[str] = []
    warnings: list[str] = []
    for r in results:
        if r.label == "malicious" and r.outcome is Outcome.APPROVED:
            failures.append(f"malicious case {r.case_id} was approved by policy")
    in_review = sum(r.outcome is Outcome.HUMAN_REVIEW for r in results)
    share = in_review / len(results)
    summary = f"{in_review} of {len(results)} cases ({share:.0%}) went to human review"
    if share > MAX_REVIEW_SHARE:
        failures.append(f"{summary}, above the {MAX_REVIEW_SHARE:.0%} cap")
    elif share > WARN_REVIEW_SHARE:
        warnings.append(f"{summary}, above the {WARN_REVIEW_SHARE:.0%} warning line")
    return Verdict(tuple(failures), tuple(warnings), share)


def _row(label: str, results: list[CaseResult]) -> dict[str, object]:
    return {
        "label": label,
        "total": len(results),
        "approved": sum(r.outcome is Outcome.APPROVED for r in results),
        "human_review": sum(r.outcome is Outcome.HUMAN_REVIEW for r in results),
        "rejected": sum(r.outcome is Outcome.REJECTED for r in results),
        "scanner_matched": sum(r.scanner_matched for r in results),
    }


def label_table(results: list[CaseResult]) -> list[dict[str, object]]:
    """One row per label, then a row for the whole set."""
    rows = [_row(label, [r for r in results if r.label == label]) for label in LABELS]
    return [*rows, _row("all", results)]
