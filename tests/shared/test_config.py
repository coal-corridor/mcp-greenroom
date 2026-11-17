"""Operability: invalid configuration stops startup with a clear message."""

from pathlib import Path

import pytest

from mcp_greenroom.config import ConfigError, load_settings


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    import os

    for key in list(os.environ):
        if key.startswith("MCP_GREENROOM_"):
            monkeypatch.delenv(key)


def test_defaults_run_with_nothing_set() -> None:
    settings = load_settings(env_file=None)
    assert settings.risk_provider == "replay"
    assert settings.recordings_dir == Path("evals/recordings")
    assert settings.approve_threshold < settings.reject_threshold


def test_out_of_range_threshold_stops_startup_with_a_clear_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MCP_GREENROOM_REJECT_THRESHOLD", "1.5")
    with pytest.raises(ConfigError) as caught:
        load_settings(env_file=None)
    message = str(caught.value)
    assert message.startswith("Invalid configuration")
    assert "MCP_GREENROOM_REJECT_THRESHOLD" in message
    assert "1.5" in message


def test_approve_threshold_must_sit_below_reject(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_GREENROOM_APPROVE_THRESHOLD", "0.9")
    monkeypatch.setenv("MCP_GREENROOM_REJECT_THRESHOLD", "0.8")
    with pytest.raises(ConfigError, match="MCP_GREENROOM_APPROVE_THRESHOLD"):
        load_settings(env_file=None)


def test_unknown_provider_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_GREENROOM_RISK_PROVIDER", "guess")
    with pytest.raises(ConfigError, match="MCP_GREENROOM_RISK_PROVIDER"):
        load_settings(env_file=None)


def test_live_provider_needs_model_and_key_and_never_echoes_the_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MCP_GREENROOM_RISK_PROVIDER", "live")
    monkeypatch.setenv("MCP_GREENROOM_MODEL_API_KEY", "synthetic-key-value-123")
    with pytest.raises(ConfigError) as caught:
        load_settings(env_file=None)
    assert "MCP_GREENROOM_MODEL" in str(caught.value)
    assert "synthetic-key-value-123" not in str(caught.value)


@pytest.mark.parametrize(
    ("variable", "value"),
    [
        ("MCP_GREENROOM_REJECT_THRESHOLD", "0.9"),
        ("MCP_GREENROOM_APPROVE_THRESHOLD", "0.1"),
        ("MCP_GREENROOM_REQUIRE_HUMAN_FOR_ALL", "true"),
    ],
)
def test_a_policy_change_without_a_new_policy_version_stops_startup(
    monkeypatch: pytest.MonkeyPatch, variable: str, value: str
) -> None:
    monkeypatch.setenv(variable, value)
    with pytest.raises(ConfigError, match="MCP_GREENROOM_POLICY_VERSION"):
        load_settings(env_file=None)
    monkeypatch.setenv("MCP_GREENROOM_POLICY_VERSION", "2026-11-17.2")
    assert load_settings(env_file=None).policy_version == "2026-11-17.2"
