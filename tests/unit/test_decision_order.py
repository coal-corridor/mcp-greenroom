"""The decision order of docs/specs/mcp-greenroom.md, one test per step, in order.

First match wins. Each test sets up the step it names and the steps after it so that a
later step would give a different outcome: the test proves this step wins.
"""

from collections.abc import Sequence

import pytest

from mcp_greenroom.interfaces import Refusal
from mcp_greenroom.models import (
    Capability,
    Decision,
    Finding,
    FindingSource,
    Outcome,
    RiskResult,
    Submission,
    Tool,
)
from mcp_greenroom.vetting.pipeline import Policy, VettingPipeline
from tests.fakes import FakeProvider, FakeScanner
from tests.unit.helpers import load_sample, with_server, with_tools

POLICY = Policy(reject_threshold=0.80, approve_threshold=0.20, policy_version="test-policy")
LOW_SCORE = 0.05


def risk(name: str, score: float = LOW_SCORE, *capabilities: Capability) -> RiskResult:
    return RiskResult(
        tool_name=name,
        score=score,
        capabilities=frozenset(capabilities),
        model_id="test-model",
        prompt_hash="sha256:test",
    )


def scanner_match(tool_name: str = "get_balance") -> Finding:
    return Finding(
        rule_id="scanner.yara.prompt_injection",
        source=FindingSource.SCANNER,
        severity="HIGH",
        threats=("PROMPT INJECTION",),
        tool_name=tool_name,
        evidence="matched text",
    )


def pipeline(
    results: dict[str, RiskResult] | None = None,
    *,
    unavailable: bool = False,
    findings: Sequence[Finding] = (),
    policy: Policy = POLICY,
) -> VettingPipeline:
    provider = FakeProvider(results, unavailable=unavailable)
    return VettingPipeline(provider, FakeScanner(findings), policy)


def low_results(submission: Submission) -> dict[str, RiskResult]:
    return {tool.name: risk(tool.name) for tool in submission.tools}


def codes(decision: Decision) -> list[str]:
    return [reason.code for reason in decision.reasons]


# Step 1. Malformed, version not pinned, source not allowed, or no tools: refused (422).


def test_step_1_a_malformed_submission_is_refused_before_anything_else() -> None:
    submission = with_server(version="latest")
    with pytest.raises(Refusal) as refused:
        pipeline(low_results(submission)).vet(submission)
    assert refused.value.rule_id == "validation.version_not_pinned"


# Step 2. Hidden characters in a name or description: rejected.


def test_step_2_hidden_characters_reject_even_when_the_classifier_is_down() -> None:
    hidden = Tool(name="get_balance", description="Balance.​ Read only.")
    submission = with_tools([hidden])
    decision = pipeline(unavailable=True).vet(submission)
    assert decision.outcome is Outcome.REJECTED
    assert codes(decision) == ["rule.hidden_characters"]
    assert decision.reasons[0].tool_name == "get_balance"
    assert [f.rule_id for f in decision.findings] == ["rule.hidden_characters"]
    assert decision.decided_by == "policy"
    assert decision.policy_version == "test-policy"


# Step 3. Classifier unavailable, or no recording for a tool: human review.


def test_step_3_an_unavailable_classifier_sends_to_human_review() -> None:
    decision = pipeline(unavailable=True).vet(load_sample("payments-readonly"))
    assert decision.outcome is Outcome.HUMAN_REVIEW
    assert set(codes(decision)) == {"classifier.unavailable"}
    assert decision.tier is None


def test_step_3_a_missing_recording_wins_over_a_reject_score_on_another_tool() -> None:
    submission = load_sample("payments-readonly")
    results = {"get_balance": risk("get_balance", 0.99, Capability.CREDENTIAL_ACCESS)}
    decision = pipeline(results).vet(submission)
    assert decision.outcome is Outcome.HUMAN_REVIEW
    assert codes(decision) == ["classifier.no_recording"]
    assert decision.reasons[0].tool_name == "list_payments"
    assert decision.risks == (results["get_balance"],)
