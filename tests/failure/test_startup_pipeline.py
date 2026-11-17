"""A pipeline that cannot be built stops startup with what failed, what was received and what
to do: no traceback, nothing served, so nothing can be approved (review finding 3)."""

import pytest

from mcp_greenroom.api import main as api_main
from mcp_greenroom.config import Settings, load_settings
from mcp_greenroom.vetting.pipeline import VettingPipeline


def test_a_pipeline_that_cannot_be_built_stops_startup_clearly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken(settings: Settings) -> VettingPipeline:
        raise ImportError("No module named 'mcpscanner'")

    monkeypatch.setattr(api_main, "build_pipeline", broken)
    monkeypatch.setattr(api_main, "load_settings", lambda: load_settings(env_file=None))
    with pytest.raises(SystemExit) as caught:
        api_main._app_or_exit()
    message = str(caught.value)
    assert message.startswith("Startup failed: the vetting pipeline could not be built.")
    assert "ImportError: No module named 'mcpscanner'" in message
    assert "uv sync" in message
