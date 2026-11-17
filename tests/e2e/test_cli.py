"""CLI conventions (edge.md): output, exit codes and inert printing."""

import json
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


@pytest.mark.parametrize(
    "env",
    [{}, {"NO_COLOR": "1", "FORCE_COLOR": "1"}],
    ids=["piped", "no-color-on-a-terminal"],
)
def test_output_has_no_colour_when_piped_or_no_color(
    monkeypatch: pytest.MonkeyPatch, env: dict[str, str]
) -> None:
    monkeypatch.setattr(cli, "TRANSPORT", _registry_listing("payments-readonly"))

    result = runner.invoke(
        app, ["client-check", str(AMP_CONFIG), "--api", "http://api.test"], env=env
    )

    assert "\x1b[3" not in result.stdout  # no foreground colour
    assert "\x1b[4" not in result.stdout  # no background colour
    assert "✗ blocked" in result.stdout  # the word carries the status, not the colour


def test_client_check_prints_server_names_inert(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    hostile = "[red]pay[/red]\x1b[2Jments​"
    config = tmp_path / "amp.json"
    entry = {"command": "npx", "args": ["-y", "@examplebank/x-mcp"]}
    config.write_text(json.dumps({"amp.mcpServers": {hostile: entry}}))
    monkeypatch.setattr(cli, "TRANSPORT", _registry_listing())

    result = runner.invoke(app, ["client-check", str(config), "--api", "http://api.test"])

    assert "[red]pay[/red]\\x1b[2Jments\\u200b" in result.stdout
    assert "\x1b[2J" not in result.stdout


def test_error_from_the_api_is_printed_inert(monkeypatch: pytest.MonkeyPatch) -> None:
    body = {"rule_id": "x[bold]y[/bold]", "message": "bad\x1b]0;t\x07", "received": "l‮atest"}

    def route(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json=body)

    monkeypatch.setattr(cli, "TRANSPORT", httpx.MockTransport(route))

    result = runner.invoke(app, ["status", "sub-1", "--api", "http://api.test"])

    assert result.exit_code == 20
    assert "x[bold]y[/bold]" in result.stderr
    assert "bad\\x1b]0;t\\x07" in result.stderr
    assert "l\\u202eatest" in result.stderr
    assert "\x1b]" not in result.stderr and "‮" not in result.stderr


@pytest.mark.parametrize("command", COMMANDS)
def test_every_command_has_help_with_one_example(command: str) -> None:
    result = runner.invoke(app, [command, "--help"])

    assert result.exit_code == 0, result.output
    assert result.stdout.count("Example: mcp-greenroom") == 1
