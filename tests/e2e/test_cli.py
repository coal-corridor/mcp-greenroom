"""CLI conventions (edge.md): output, exit codes and inert printing."""

from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

from mcp_greenroom import cli
from mcp_greenroom.cli import app

ROOT = Path(__file__).resolve().parents[2]
AMP_CONFIG = ROOT / "sample-data" / "client-configs" / "amp-settings.json"

runner = CliRunner()

COMMANDS = ("submit", "status", "review", "audit", "list", "client-check", "health")


def test_bare_command_prints_name_tagline_and_commands() -> None:
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "mcp-greenroom" in result.stdout
    assert "vetted" in result.stdout.lower()
    for command in COMMANDS:
        assert command in result.stdout


def _registry_listing(*identifiers: str) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v0.1/servers"
        records = [
            {
                "server": {
                    "name": f"com.examplebank/{i}",
                    "packages": [{"registryType": "npm", "identifier": f"@examplebank/{i}-mcp"}],
                }
            }
            for i in identifiers
        ]
        return httpx.Response(200, json={"servers": records})

    return httpx.MockTransport(handler)


@pytest.mark.parametrize(
    ("listed", "code", "line"),
    [
        (("payments-readonly", "poisoned-notes"), 0, "✓ allowed"),
        (("payments-readonly",), 20, "✗ blocked"),
    ],
    ids=["all-allowed", "one-blocked"],
)
def test_client_check_exit_code(
    monkeypatch: pytest.MonkeyPatch, listed: tuple[str, ...], code: int, line: str
) -> None:
    monkeypatch.setattr(cli, "TRANSPORT", _registry_listing(*listed), raising=False)

    result = runner.invoke(app, ["client-check", str(AMP_CONFIG), "--api", "http://api.test"])

    assert result.exit_code == code, result.output
    assert line in result.stdout
    assert "simulat" in result.stdout.lower()
