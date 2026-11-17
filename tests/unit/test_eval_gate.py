"""Classifier evaluation gate: no malicious sample approved, at most half in review."""

from evals.gate import CaseResult, judge, label_table

from mcp_greenroom.models import Outcome

A, R, X = Outcome.APPROVED, Outcome.HUMAN_REVIEW, Outcome.REJECTED


def cases(*specs: tuple[str, Outcome], scanner: int = 0) -> list[CaseResult]:
    return [
        CaseResult(f"c{i}", label, outcome, (), scanner_matched=i < scanner)
        for i, (label, outcome) in enumerate(specs)
    ]


def test_a_clean_run_passes_without_warnings() -> None:
    verdict = judge(cases(("benign", A), ("benign", A), ("malicious", X), ("ambiguous", R)))
    assert verdict.passed
    assert verdict.warnings == ()
    assert verdict.review_share == 0.25


def test_one_malicious_sample_approved_fails_the_gate() -> None:
    verdict = judge(cases(("benign", A), ("malicious", A), ("malicious", X), ("benign", A)))
    assert not verdict.passed
    assert any("c1" in failure for failure in verdict.failures)


def test_more_than_half_in_review_fails_the_gate() -> None:
    verdict = judge(cases(("benign", R), ("benign", R), ("benign", R), ("malicious", X)))
    assert not verdict.passed
    assert verdict.review_share == 0.75


def test_exactly_half_in_review_passes_with_a_warning() -> None:
    verdict = judge(cases(("benign", R), ("benign", R), ("benign", A), ("malicious", X)))
    assert verdict.passed
    assert verdict.warnings


def test_above_thirty_percent_in_review_is_a_warning() -> None:
    specs = [("benign", A)] * 6 + [("ambiguous", R)] * 4
    verdict = judge(cases(*specs))
    assert verdict.passed
    assert len(verdict.warnings) == 1


def test_an_empty_set_fails_the_gate() -> None:
    assert not judge([]).passed


def test_the_table_counts_outcomes_and_scanner_matches_per_label() -> None:
    results = cases(("benign", A), ("malicious", X), ("malicious", R), ("ambiguous", R), scanner=2)
    rows = {row["label"]: row for row in label_table(results)}
    assert rows["benign"] == {
        "label": "benign",
        "total": 1,
        "approved": 1,
        "human_review": 0,
        "rejected": 0,
        "scanner_matched": 1,
    }
    assert rows["malicious"]["rejected"] == 1
    assert rows["malicious"]["human_review"] == 1
    assert rows["malicious"]["scanner_matched"] == 1
    assert rows["all"]["total"] == 4
