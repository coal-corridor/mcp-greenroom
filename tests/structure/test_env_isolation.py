"""Every test runs on the defaults: no MCP_GREENROOM_* variable from the shell, the key included.

The clearing fixture lives in tests/conftest.py, so it covers api, e2e, failure and every other
folder, not only unit. This test sits outside unit on purpose.
"""

import os

import pytest


def test_every_test_folder_clears_the_shell_settings(request: pytest.FixtureRequest) -> None:
    assert "_clean_greenroom_env" in request.fixturenames
    assert [name for name in os.environ if name.startswith("MCP_GREENROOM_")] == []
