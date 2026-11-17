"""Edge test setup: the CLI's settings never come from the developer's .env file."""

import pytest

from mcp_greenroom import cli
from mcp_greenroom.config import load_settings


@pytest.fixture(autouse=True)
def _settings_without_env_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "load_settings", lambda: load_settings(env_file=None))
