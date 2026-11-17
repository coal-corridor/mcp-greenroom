"""The mcp-greenroom command. Talks to the API over HTTP only."""

import typer
from rich.console import Console
from rich.table import Table

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

app = typer.Typer(add_completion=False, no_args_is_help=False)


def _out() -> Console:
    return Console(highlight=False, soft_wrap=True)


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
