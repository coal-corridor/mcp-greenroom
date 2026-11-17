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
    raise NotImplementedError


def label_table(results: list[CaseResult]) -> list[dict[str, object]]:
    raise NotImplementedError
