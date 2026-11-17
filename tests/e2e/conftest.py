"""Edge test setup: the CLI's settings never come from the developer's .env file, and the
terminal width is fixed."""

import pytest

from mcp_greenroom import cli
from mcp_greenroom.config import load_settings


@pytest.fixture(autouse=True)
def _settings_without_env_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "load_settings", lambda: load_settings(env_file=None))


@pytest.fixture(autouse=True)
def _fixed_terminal_width(monkeypatch: pytest.MonkeyPatch) -> None:
    """Rich sizes its output from COLUMNS. A fixed width keeps every CLI assertion independent of
    the shell that runs the tests: a 64-column shell wrapped a table cell across two lines."""
    monkeypatch.setenv("COLUMNS", "120")
