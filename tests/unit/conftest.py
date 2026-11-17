"""Unit tests run on the defaults: no MCP_GREENROOM_* variable from the shell leaks in."""

import os

import pytest


@pytest.fixture(autouse=True)
def _clean_greenroom_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.startswith("MCP_GREENROOM_"):
            monkeypatch.delenv(name)
