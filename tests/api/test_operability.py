"""Operability (registry spec): health, one log line per request and decision, config check."""

import json
import logging
import os
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from mcp_greenroom.logging import LOGGER_NAME
from tests.api.conftest import DANA, RILEY, SAM, sample


def _events(caplog: pytest.LogCaptureFixture, event: str) -> list[dict[str, object]]:
    lines = [json.loads(r.getMessage()) for r in caplog.records if r.name == LOGGER_NAME]
    return [line for line in lines if line["event"] == event]


@pytest.fixture(autouse=True)
def _capture(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger=LOGGER_NAME)


def test_each_request_writes_one_log_line(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.clear()
    client.get("/livez")
    client.get("/v0.1/servers")

    lines = _events(caplog, "http.request")
    assert [(line["method"], line["path"], line["status"]) for line in lines] == [
        ("GET", "/livez", 200),
        ("GET", "/v0.1/servers", 200),
    ]
    assert all(isinstance(line["duration_ms"], float) for line in lines)


def test_each_decision_writes_one_log_line(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.clear()
    pending = client.post("/submissions", json=sample("ambiguous-exporter"), headers=RILEY)
    client.post(
        f"/submissions/{pending.json()['submission_id']}/review",
        json={"action": "approve", "note": "ok"},
        headers=SAM,
    )

    lines = _events(caplog, "decision")
    assert [(line["outcome"], line["decided_by"]) for line in lines] == [
        ("human_review", "policy"),
        ("approved", "sam"),
    ]
    for line in lines:
        assert line["submission_id"] == pending.json()["submission_id"]
        assert line["policy_version"]


def test_logs_carry_no_tool_text(client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
    poisoned = sample("poisoned-notes")
    client.post("/submissions", json=poisoned, headers=DANA)

    for tool in poisoned["tools"]:
        assert tool["description"] not in caplog.text


def test_invalid_configuration_stops_startup_with_a_clear_message() -> None:
    env = {**os.environ, "MCP_GREENROOM_REJECT_THRESHOLD": "lots"}
    result = subprocess.run(
        [sys.executable, "-c", "import mcp_greenroom.api.main"],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode != 0
    assert "Invalid configuration" in result.stderr
    assert "MCP_GREENROOM_REJECT_THRESHOLD" in result.stderr
    assert "Traceback" not in result.stderr
