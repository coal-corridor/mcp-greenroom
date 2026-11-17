"""End to end: the CLI drives the main samples through the real app over localhost HTTP.

The app runs with the contracts FakePipeline (tests/e2e/fake_service.py) until vetting merges.
Skipped while the API package is not on this branch (area/registry merges it).
"""

import json
import socket
import threading
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

pytest.importorskip("mcp_greenroom.api.main", reason="the API is not merged on this branch yet")

import uvicorn  # noqa: E402

from mcp_greenroom import cli  # noqa: E402
from mcp_greenroom.cli import app  # noqa: E402
from tests.e2e.fake_service import build_app  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "sample-data" / "servers"
AMP_CONFIG = ROOT / "sample-data" / "client-configs" / "amp-settings.json"

runner = CliRunner()


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port: int = sock.getsockname()[1]
        return port


@pytest.fixture
def api_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    monkeypatch.setattr(cli, "TRANSPORT", None)
    port = _free_port()
    config = uvicorn.Config(build_app(tmp_path), host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started:
        assert time.monotonic() < deadline, "the API did not start within 10 s"
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=10)


def run(api_url: str, token: str, *args: str) -> Any:
    return runner.invoke(app, [*args, "--api", api_url, "--token", token])


def submit(api_url: str, token: str, sample: str) -> Any:
    return run(api_url, token, "submit", str(SAMPLES / f"{sample}.json"), "--json")


def test_cli_drives_the_main_samples_end_to_end(api_url: str) -> None:
    approved = submit(api_url, "dev-dana", "payments-readonly")
    assert approved.exit_code == 0, approved.output
    assert json.loads(approved.stdout)["tier"] == "low"

    listed = run(api_url, "dev-dana", "list")
    assert listed.exit_code == 0, listed.output
    assert "com.examplebank/payments-readonly 1.2.0" in listed.stdout

    checked = run(api_url, "dev-dana", "client-check", str(AMP_CONFIG))
    assert checked.exit_code == 20, checked.output
    assert "✓ allowed  payments" in checked.stdout
    assert "✗ blocked  notes" in checked.stdout

    refused = submit(api_url, "dev-dana", "invalid-unpinned")
    assert refused.exit_code == 20, refused.output

    rejected = submit(api_url, "dev-dana", "poisoned-notes")
    assert rejected.exit_code == 20, rejected.output

    abstained = submit(api_url, "dev-dana", "unrecorded-reporter")
    assert abstained.exit_code == 10, abstained.output

    review = submit(api_url, "dev-dana", "ambiguous-exporter")
    assert review.exit_code == 10, review.output
    case = json.loads(review.stdout)["submission_id"]

    own = run(api_url, "dev-dana", "review", case, "--approve", "--note", "Mine.")
    assert own.exit_code == 20, own.output
    other = run(api_url, "dev-riley", "review", case, "--approve", "--note", "Checked.")
    assert other.exit_code == 0, other.output

    status = run(api_url, "dev-sam", "status", case)
    assert status.exit_code == 0, status.output
    assert "✓ approved" in status.stdout

    trail = run(api_url, "dev-sam", "audit", case)
    assert trail.exit_code == 0, trail.output
    assert "riley" in trail.stdout

    health = run(api_url, "dev-sam", "health")
    assert health.exit_code == 0, health.output
