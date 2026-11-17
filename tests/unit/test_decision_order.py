"""The decision order of docs/specs/mcp-greenroom.md, one test per step, in order.

First match wins. Each test sets up the step it names and the steps after it so that a
later step would give a different outcome: the test proves this step wins.
"""

from collections.abc import Sequence

import pytest

from mcp_greenroom.interfaces import Refusal
from mcp_greenroom.models import (
    Capability,
    Finding,
    FindingSource,
    RiskResult,
    Submission,
)
from mcp_greenroom.vetting.pipeline import Policy, VettingPipeline
from tests.fakes import FakeProvider, FakeScanner
from tests.unit.helpers import with_server

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


def codes(decision: object) -> list[str]:
    return [reason.code for reason in decision.reasons]  # type: ignore[attr-defined]


# Step 1. Malformed, version not pinned, source not allowed, or no tools: refused (422).


def test_step_1_a_malformed_submission_is_refused_before_anything_else() -> None:
    submission = with_server(version="latest")
    with pytest.raises(Refusal) as refused:
        pipeline(low_results(submission)).vet(submission)
    assert refused.value.rule_id == "validation.version_not_pinned"
