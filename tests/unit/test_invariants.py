"""Invariants of docs/specs/mcp-greenroom.md that hold on every path of the pipeline."""

import pytest

from mcp_greenroom.models import Capability, Outcome, Tool
from tests.unit.helpers import load_sample, with_tools
from tests.unit.test_decision_order import (
    low_results,
    pipeline,
    risk,
    scanner_match,
)

PAYMENTS = load_sample("payments-readonly")
HIDDEN = with_tools([Tool(name="get_balance", description="Balance.​")])


@pytest.mark.parametrize(
    ("submission", "results", "outcome"),
    [
        (HIDDEN, {}, Outcome.REJECTED),  # step 2
        (PAYMENTS, {}, Outcome.HUMAN_REVIEW),  # step 3
        (PAYMENTS, {"get_balance": risk("get_balance", 0.9)}, Outcome.REJECTED),  # step 4
        (PAYMENTS, {"get_balance": risk("get_balance", 0.5)}, Outcome.HUMAN_REVIEW),  # step 5
        (
            PAYMENTS,
            {"get_balance": risk("get_balance", 0.05, Capability.CODE_EXEC)},
            Outcome.HUMAN_REVIEW,
        ),  # step 7 would apply without the match; step 6 wins
    ],
)
def test_scanner_findings_are_shown_with_every_outcome(
    submission: object, results: dict[str, object], outcome: Outcome
) -> None:
    match = scanner_match("get_balance")
    full = low_results(PAYMENTS) | results if results else {}
    decision = pipeline(full, findings=[match]).vet(submission)  # type: ignore[arg-type]
    assert decision.outcome is outcome
    assert match in decision.findings
