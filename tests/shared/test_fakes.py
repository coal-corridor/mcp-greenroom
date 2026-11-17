"""The fakes reach the outcomes in sample-data/servers/README.md and fail closed."""

from pathlib import Path

import pytest

from mcp_greenroom.interfaces import ClassifierUnavailable, NoRecording, Refusal
from mcp_greenroom.models import Outcome, RiskResult, Submission, Tier, Tool
from tests.fakes import FakePipeline, FakeProvider

SAMPLES = Path(__file__).resolve().parents[2] / "sample-data" / "servers"


def _load(slug: str) -> Submission:
    return Submission.model_validate_json((SAMPLES / f"{slug}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("slug", "outcome", "tier"),
    [
        ("payments-readonly", Outcome.APPROVED, Tier.LOW),
        ("poisoned-notes", Outcome.REJECTED, Tier.HIGH),
        ("unrecorded-reporter", Outcome.HUMAN_REVIEW, None),
        ("ambiguous-exporter", Outcome.HUMAN_REVIEW, Tier.MEDIUM),
    ],
)
def test_fake_pipeline_reaches_the_table_outcome(slug: str, outcome: Outcome, tier: Tier) -> None:
    decision = FakePipeline().vet(_load(slug))
    assert (decision.outcome, decision.tier) == (outcome, tier)


def test_fake_pipeline_refuses_the_unpinned_sample() -> None:
    with pytest.raises(Refusal):
        FakePipeline().vet(_load("invalid-unpinned"))


def test_fake_pipeline_sends_an_unknown_server_to_review() -> None:
    unknown = Submission(server={"name": "com.examplebank/other", "version": "1.0.0"}, tools=[])
    assert FakePipeline().vet(unknown).outcome is Outcome.HUMAN_REVIEW


def test_fake_provider_signals_both_failures() -> None:
    tool = Tool(name="t", description="d")
    with pytest.raises(NoRecording):
        FakeProvider().classify(tool)
    with pytest.raises(ClassifierUnavailable):
        FakeProvider(unavailable=True).classify(tool)
    result = RiskResult(tool_name="t", score=0.1, model_id="fake", prompt_hash="p")
    assert FakeProvider({"t": result}).classify(tool) == result
