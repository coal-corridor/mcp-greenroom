"""Invariants of docs/specs/mcp-greenroom.md that hold on every path of the pipeline."""

import pytest

from mcp_greenroom.models import Capability, Outcome, Tool
from mcp_greenroom.vetting.pipeline import VettingPipeline
from tests.fakes import FakeProvider, FakeScanner
from tests.unit.helpers import load_sample, with_tools
from tests.unit.test_decision_order import (
    POLICY,
    BrokenScanner,
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


class OddProvider:
    """A provider that fails in a way the interface does not name."""

    def __init__(self, behaviour: str) -> None:
        self.behaviour = behaviour

    def classify(self, tool: Tool) -> object:
        if self.behaviour == "raises_runtime_error":
            raise RuntimeError("boom")
        if self.behaviour == "raises_value_error":
            raise ValueError("bad json")
        if self.behaviour == "returns_none":
            return None
        if self.behaviour == "answers_for_another_tool":
            return risk("some_other_tool")
        if self.behaviour == "answers_for_the_first_tool_only":
            return risk("get_balance")
        raise AssertionError(self.behaviour)


ODD = [
    "raises_runtime_error",
    "raises_value_error",
    "returns_none",
    "answers_for_another_tool",
    "answers_for_the_first_tool_only",
]


@pytest.mark.parametrize("behaviour", ODD)
def test_provider_failure_never_approves(behaviour: str) -> None:
    pipe = VettingPipeline(OddProvider(behaviour), FakeScanner(), POLICY)  # type: ignore[arg-type]
    decision = pipe.vet(PAYMENTS)
    assert decision.outcome is Outcome.HUMAN_REVIEW
    assert decision.reasons


@pytest.mark.parametrize("unavailable", [True, False])
def test_named_provider_failures_never_approve(unavailable: bool) -> None:
    decision = pipeline({}, unavailable=unavailable).vet(PAYMENTS)
    assert decision.outcome is Outcome.HUMAN_REVIEW


@pytest.mark.parametrize("severity", ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
def test_a_scanner_match_never_approves_and_never_rejects_alone(severity: str) -> None:
    match = scanner_match("get_balance").model_copy(update={"severity": severity})
    decision = pipeline(low_results(PAYMENTS), findings=[match]).vet(PAYMENTS)
    assert decision.outcome is Outcome.HUMAN_REVIEW


def test_a_scanner_failure_never_approves() -> None:
    pipe = VettingPipeline(FakeProvider(low_results(PAYMENTS)), BrokenScanner(), POLICY)
    assert pipe.vet(PAYMENTS).outcome is Outcome.HUMAN_REVIEW
