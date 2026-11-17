"""The decision order of docs/specs/mcp-greenroom.md, one test per step, in order.

First match wins. Each test sets up the step it names and the steps after it so that a
later step would give a different outcome: the test proves this step wins.
"""

from collections.abc import Sequence

import pytest

from mcp_greenroom.interfaces import Refusal, ScannerError
from mcp_greenroom.models import (
    Capability,
    Decision,
    Finding,
    FindingSource,
    Outcome,
    RiskResult,
    Submission,
    Tier,
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


# Step 4. Highest risk score at or above the reject threshold: rejected.


@pytest.mark.parametrize("score", [0.80, 0.97])
def test_step_4_a_score_at_the_reject_threshold_rejects(score: float) -> None:
    submission = load_sample("poisoned-notes")
    results = low_results(submission) | {"search_notes": risk("search_notes", score)}
    decision = pipeline(results, findings=[scanner_match("search_notes")]).vet(submission)
    assert decision.outcome is Outcome.REJECTED
    assert codes(decision) == ["classifier.reject_threshold"]
    assert decision.reasons[0].tool_name == "search_notes"


def test_step_4_the_rejection_names_the_rule_the_tool_and_the_offending_text() -> None:
    submission = load_sample("poisoned-notes")
    results = low_results(submission) | {"search_notes": risk("search_notes", 0.95)}
    decision = pipeline(results).vet(submission)
    classifier = [f for f in decision.findings if f.source is FindingSource.CLASSIFIER]
    assert [(f.rule_id, f.tool_name) for f in classifier] == [
        ("classifier.reject_threshold", "search_notes")
    ]
    description = submission.tools[0].description
    assert classifier[0].evidence == description
    assert "0.95" in decision.reasons[0].message


# Step 5. Highest risk score at or above the approve threshold: human review.


@pytest.mark.parametrize("score", [0.20, 0.79])
def test_step_5_an_uncertain_score_sends_a_low_tier_server_to_human_review(score: float) -> None:
    submission = load_sample("payments-readonly")
    results = low_results(submission) | {"list_payments": risk("list_payments", score)}
    decision = pipeline(results, findings=[scanner_match()]).vet(submission)
    assert decision.outcome is Outcome.HUMAN_REVIEW
    assert codes(decision) == ["classifier.uncertain"]
    assert decision.reasons[0].tool_name == "list_payments"
    assert decision.tier is Tier.LOW


# Step 6. A scanner rule matched on any tool: human review.


class BrokenScanner:
    def scan(self, tools: Sequence[Tool]) -> list[Finding]:
        raise ScannerError("scanner output unreadable")


def test_step_6_a_scanner_match_sends_a_low_tier_server_to_human_review() -> None:
    submission = load_sample("payments-readonly")
    match = scanner_match("list_payments")
    decision = pipeline(low_results(submission), findings=[match]).vet(submission)
    assert decision.outcome is Outcome.HUMAN_REVIEW
    assert codes(decision) == ["scanner.match"]
    assert decision.reasons[0].tool_name == "list_payments"
    assert match in decision.findings
    assert decision.tier is Tier.LOW


def test_step_6_a_scanner_that_fails_sends_to_human_review() -> None:
    submission = load_sample("payments-readonly")
    provider = FakeProvider(low_results(submission))
    decision = VettingPipeline(provider, BrokenScanner(), POLICY).vet(submission)
    assert decision.outcome is Outcome.HUMAN_REVIEW
    assert codes(decision) == ["scanner.unavailable"]


# Step 7. Tier medium or high: human review.


@pytest.mark.parametrize(
    ("capabilities", "tier"),
    [
        ({"list_payments": [Capability.NETWORK_EGRESS]}, Tier.MEDIUM),
        ({"get_balance": [Capability.CODE_EXEC]}, Tier.HIGH),
        # The tier spans the server: one tool reads, another sends.
        (
            {
                "get_balance": [Capability.LOCAL_READ],
                "list_payments": [Capability.NETWORK_EGRESS],
            },
            Tier.HIGH,
        ),
    ],
)
def test_step_7_a_medium_or_high_tier_sends_to_human_review(
    capabilities: dict[str, list[Capability]], tier: Tier
) -> None:
    submission = load_sample("payments-readonly")
    results = low_results(submission) | {
        name: risk(name, LOW_SCORE, *caps) for name, caps in capabilities.items()
    }
    decision = pipeline(results).vet(submission)
    assert decision.outcome is Outcome.HUMAN_REVIEW
    assert decision.tier is tier
    assert codes(decision) == [f"tier.{tier.value}"]
