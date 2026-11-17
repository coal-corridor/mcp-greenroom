"""CLI status, review, audit and list (edge.md), against bodies in area/registry's route shapes.

Routes read from area/registry: GET /submissions/{id}, POST /submissions/{id}/review
({action, note}), GET /submissions/{id}/audit ({submission_id, events}), GET /v0.1/servers.
"""

import json
from collections.abc import Callable

import httpx
import pytest
from typer.testing import CliRunner

from mcp_greenroom import cli
from mcp_greenroom.cli import app
from tests.e2e.test_cli_submit import result_body

runner = CliRunner()
API = ["--api", "http://api.test", "--token", "dev-riley"]


def api(route: Callable[[httpx.Request], httpx.Response]) -> httpx.MockTransport:
    return httpx.MockTransport(route)


@pytest.mark.parametrize(
    ("sample", "code", "word"),
    [
        ("payments-readonly", 0, "✓ approved"),
        ("ambiguous-exporter", 10, "! needs review"),
        ("poisoned-notes", 20, "✗ rejected"),
    ],
)
def test_status_shows_the_decision_with_exit_code(
    monkeypatch: pytest.MonkeyPatch, sample: str, code: int, word: str
) -> None:
    body = result_body(sample)

    def route(request: httpx.Request) -> httpx.Response:
        assert (request.method, request.url.path) == ("GET", f"/submissions/sub-{sample}")
        return httpx.Response(200, json=body)

    monkeypatch.setattr(cli, "TRANSPORT", api(route))

    result = runner.invoke(app, ["status", f"sub-{sample}", *API])
    as_json = runner.invoke(app, ["status", f"sub-{sample}", *API, "--json"])

    assert result.exit_code == code, result.output
    assert word in result.stdout
    assert json.loads(as_json.stdout) == body
    assert as_json.exit_code == code
