"""The eval stage gates on recordings and default thresholds, whatever the shell says."""

import pytest
from evals.run_eval import eval_settings
from pydantic import SecretStr

from mcp_greenroom.config import Settings


def test_the_eval_forces_replay_and_the_default_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_GREENROOM_RISK_PROVIDER", "live")
    monkeypatch.setenv("MCP_GREENROOM_MODEL", "claude-test-model")
    monkeypatch.setenv("MCP_GREENROOM_MODEL_API_KEY", "test-key-not-a-secret")
    monkeypatch.setenv("MCP_GREENROOM_REJECT_THRESHOLD", "0.99")
    monkeypatch.setenv("MCP_GREENROOM_APPROVE_THRESHOLD", "0.5")
    monkeypatch.setenv("MCP_GREENROOM_REQUIRE_HUMAN_FOR_ALL", "true")
    monkeypatch.setenv("MCP_GREENROOM_POLICY_VERSION", "shell-policy-2")  # required with a change
    settings = eval_settings()
    defaults = Settings.model_fields
    assert settings.risk_provider == "replay"
    assert settings.model_api_key is None or isinstance(settings.model_api_key, SecretStr)
    assert settings.reject_threshold == defaults["reject_threshold"].default
    assert settings.approve_threshold == defaults["approve_threshold"].default
    assert settings.require_human_for_all is False
    assert settings.policy_version == defaults["policy_version"].default
