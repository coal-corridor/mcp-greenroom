"""The pipeline is built from configuration: replay by default, live only when asked."""

from pathlib import Path

from pydantic import SecretStr

from mcp_greenroom.config import Settings
from mcp_greenroom.models import Outcome
from mcp_greenroom.risk.live import LiveProvider
from mcp_greenroom.risk.replay import ReplayProvider
from mcp_greenroom.scanner.null import NullScanner
from mcp_greenroom.vetting.factory import build_pipeline
from tests.unit.helpers import load_sample


def defaults() -> Settings:
    return Settings(_env_file=None)  # type: ignore[call-arg]


def test_the_default_pipeline_replays_recordings() -> None:
    pipe = build_pipeline(defaults())
    assert isinstance(pipe.provider, ReplayProvider)
    assert pipe.provider.recordings_dir == Path("evals/recordings")
    assert isinstance(pipe.scanner, NullScanner)
    assert pipe.policy.reject_threshold == 0.80
    assert pipe.policy.approve_threshold == 0.20
    assert pipe.policy.policy_version == defaults().policy_version


def test_the_live_provider_is_built_only_when_configured() -> None:
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        risk_provider="live",
        model="claude-test-model",
        model_api_key=SecretStr("k"),
        model_base_url="https://models.example.test",
    )
    provider = build_pipeline(settings).provider
    assert isinstance(provider, LiveProvider)
    assert (provider.base_url, provider.model) == (
        "https://models.example.test",
        "claude-test-model",
    )


def test_unrecorded_reporter_abstains_into_human_review() -> None:
    # Abstain criterion, on the real recordings directory: this sample is never recorded.
    decision = build_pipeline(defaults()).vet(load_sample("unrecorded-reporter"))
    assert decision.outcome is Outcome.HUMAN_REVIEW
    assert [r.code for r in decision.reasons] == ["classifier.no_recording"]
    assert decision.reasons[0].tool_name == "monthly_summary"
