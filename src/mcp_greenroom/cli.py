"""The mcp-greenroom command. Talks to the API over HTTP only."""

from pathlib import Path
from typing import Annotated, NoReturn

import httpx
import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from mcp_greenroom.client_sim import check_config
from mcp_greenroom.config import ConfigError, load_settings

NAME = "mcp-greenroom"
TAGLINE = "Vetted intake for MCP servers."

COMMANDS = (
    ("submit FILE", "Send one server version for vetting."),
    ("status ID", "Show a submission and its decision."),
    ("review ID", "Approve or decline a case in human review."),
    ("audit ID", "List the audit records of a submission."),
    ("list", "List the approved versions on the registry."),
    ("client-check CONFIG", "Simulate a client's registry check on a config."),
    ("health", "Show liveness, readiness and registry mode."),
)

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_REVIEW = 10
EXIT_REJECTED = 20

# Tests swap in an httpx.MockTransport here. None means a real connection.
TRANSPORT: httpx.BaseTransport | None = None
TIMEOUT_SECONDS = 10.0

app = typer.Typer(add_completion=False, no_args_is_help=False)

ApiOption = Annotated[
    str | None, typer.Option("--api", help="API address. Default: MCP_GREENROOM_API.")
]
TokenOption = Annotated[
    str | None, typer.Option("--token", help="Bearer token. Default: MCP_GREENROOM_TOKEN.")
]


def _out() -> Console:
    return Console(highlight=False, soft_wrap=True)


def _err() -> Console:
    return Console(stderr=True, highlight=False, soft_wrap=True)


def _fail(what: str, received: str, todo: str, code: int = EXIT_FAILURE) -> NoReturn:
    """Print a three-part error to standard error and exit."""
    err = _err()
    err.print(Text.assemble(("Error: ", "bold red"), what))
    err.print(Text(f"  Received: {received}"))
    err.print(Text(f"  Next: {todo}"))
    raise typer.Exit(code)


def _next(step: str) -> None:
    _out().print(Text(f"Next: {step}", style="dim"))


def _client(api: str | None, token: str | None) -> httpx.Client:
    """The one place the CLI opens an HTTP connection."""
    try:
        settings = load_settings()
    except ConfigError as exc:
        _fail("Invalid configuration.", str(exc), "Fix the variable named above.")
    base = api or settings.api
    secret = token or (settings.token.get_secret_value() if settings.token else None)
    headers = {"Authorization": f"Bearer {secret}"} if secret else {}
    return httpx.Client(
        base_url=base, headers=headers, transport=TRANSPORT, timeout=TIMEOUT_SECONDS
    )


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Vetted intake for MCP servers.

    Example: mcp-greenroom submit sample-data/servers/payments-readonly.json
    """
    if ctx.invoked_subcommand is not None:
        return
    out = _out()
    out.print(f"[bold]{NAME}[/bold]  {TAGLINE}")
    table = Table.grid(padding=(0, 2))
    for usage, summary in COMMANDS:
        table.add_row(f"  {NAME} {usage}", summary)
    out.print(table)
    out.print(f"[dim]Next: {NAME} --help, or {NAME} COMMAND --help[/dim]")


@app.command("client-check")
def client_check(
    config: Annotated[Path, typer.Argument(help="Client config file (Amp settings shape).")],
    api: ApiOption = None,
) -> None:
    """Simulate a client's registry check: allowed or blocked, per local server.

    Example: mcp-greenroom client-check sample-data/client-configs/amp-settings.json
    """
    try:
        with _client(api, None) as registry:
            verdicts = check_config(config, registry)
    except (OSError, ValueError, KeyError) as exc:
        _fail(
            "Could not read the client config.",
            f"{config} ({type(exc).__name__})",
            "Pass a JSON file with an 'amp.mcpServers' object.",
            EXIT_FAILURE,
        )
    out = _out()
    out.print(Text("Simulation of Amp's documented registry check, not Amp itself."))
    for verdict in verdicts:
        mark = ("✓ allowed", "green") if verdict.allowed else ("✗ blocked", "red")
        out.print(Text.assemble(mark, "  ", verdict.server, "  ", (verdict.reason, "dim")))
    if all(v.allowed for v in verdicts):
        _next(f"{NAME} list, to see every approved version")
        return
    _next(f"submit the blocked server with {NAME} submit FILE, or remove it from the config")
    raise typer.Exit(EXIT_REJECTED)
