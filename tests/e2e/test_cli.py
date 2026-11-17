"""CLI conventions (edge.md): output, exit codes and inert printing."""

from typer.testing import CliRunner

from mcp_greenroom.cli import app

runner = CliRunner()

COMMANDS = ("submit", "status", "review", "audit", "list", "client-check", "health")


def test_bare_command_prints_name_tagline_and_commands() -> None:
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "mcp-greenroom" in result.stdout
    assert "vetted" in result.stdout.lower()
    for command in COMMANDS:
        assert command in result.stdout
