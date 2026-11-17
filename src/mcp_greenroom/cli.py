"""The mcp-greenroom command. Talks to the API over HTTP only."""

import json
import sys
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import quote

import httpx
import typer
from rich.table import Table
from rich.text import Text

from mcp_greenroom.cli_output import (
    EXIT_FAILURE,
    EXIT_OK,
    EXIT_REJECTED,
    NAME,
    error_body,
    exit_code,
    fail,
    fail_from,
    inert,
    next_step,
    show_decision,
    stdout_console,
)
from mcp_greenroom.client_sim import check_config
from mcp_greenroom.config import ConfigError, load_settings

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

# Tests swap in an httpx.MockTransport here. None means a real connection.
TRANSPORT: httpx.BaseTransport | None = None

TIMEOUT_SECONDS = 10.0
MAX_PAGES = 1000
DEGRADED_HEADER = "X-Greenroom-Degraded"  # set by GET /v0.1/servers when serving last-good
GENERATED_AT_HEADER = "X-Greenroom-Generated-At"

app = typer.Typer(add_completion=False, no_args_is_help=False)

ApiOption = Annotated[
    str | None, typer.Option("--api", help="API address. Default: MCP_GREENROOM_API.")
]
TokenOption = Annotated[
    str | None, typer.Option("--token", help="Bearer token. Default: MCP_GREENROOM_TOKEN.")
]

JsonOption = Annotated[
    bool, typer.Option("--json", help="Print the API response body as JSON, nothing else.")
]


def _client(api: str | None, token: str | None) -> httpx.Client:
    """The one place the CLI opens an HTTP connection."""
    try:
        settings = load_settings()
    except ConfigError as exc:
        fail("Invalid configuration.", str(exc), "Fix the variable named above.")
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
    out = stdout_console()
    out.print(f"[bold]{NAME}[/bold]  {TAGLINE}")
    table = Table.grid(padding=(0, 2))
    for usage, summary in COMMANDS:
        table.add_row(f"  {NAME} {usage}", summary)
    out.print(table)
    out.print(f"[dim]Next: {NAME} --help, or {NAME} COMMAND --help[/dim]")


def _send(method: str, path: str, api: str | None, token: str | None, **kwargs: Any) -> Any:
    """Send one request and return the response. Exits with a clear error if unreachable."""
    with _client(api, token) as client:
        try:
            return client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            fail(
                f"The API is unreachable ({type(exc).__name__}).",
                f"{method} {client.base_url.join(path)}",
                "Start it with 'make run', or pass the right address with --api.",
            )


def _json(response: httpx.Response) -> Any:
    """The JSON body of a 2xx answer, or exit with the API's error."""
    if not response.is_success:
        fail_from(response)
    try:
        return response.json()
    except ValueError:
        fail("The API answer is not JSON.", f"HTTP {response.status_code}", "Check --api.")


def _call(
    method: str, path: str, api: str | None, token: str | None, as_json: bool, **kwargs: Any
) -> Any:
    """Send one request and return its JSON body. With as_json, also print the body unchanged,
    alone on standard output."""
    response = _send(method, path, api, token, **kwargs)
    if as_json and response.content:
        sys.stdout.write(response.text.rstrip("\n") + "\n")
    return _json(response)


@app.command()
def submit(
    file: Annotated[Path, typer.Argument(help="Submission file: server.json and tools.")],
    api: ApiOption = None,
    token: TokenOption = None,
    as_json: JsonOption = False,
) -> None:
    """Send one server version for vetting.

    Example: mcp-greenroom submit sample-data/servers/payments-readonly.json
    """
    try:
        payload = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        fail(
            "Could not read the submission file.",
            f"{file} ({type(exc).__name__})",
            "Pass a JSON file with 'server' and 'tools'.",
        )
    body = _call("POST", "/submissions", api, token, as_json, json=payload)
    raise typer.Exit(exit_code(body) if as_json else show_decision(body))


IdArgument = Annotated[str, typer.Argument(help="Submission id, as submit printed it.")]


@app.command()
def status(
    submission_id: IdArgument,
    api: ApiOption = None,
    token: TokenOption = None,
    as_json: JsonOption = False,
) -> None:
    """Show a submission and its decision.

    Example: mcp-greenroom status 3f2c9a1e-...
    """
    body = _call("GET", f"/submissions/{quote(submission_id, safe='')}", api, token, as_json)
    raise typer.Exit(exit_code(body) if as_json else show_decision(body))


@app.command()
def review(
    submission_id: IdArgument,
    note: Annotated[str, typer.Option("--note", help="Why: recorded with the decision.")],
    approve: Annotated[bool, typer.Option("--approve", help="Approve the case.")] = False,
    decline: Annotated[bool, typer.Option("--decline", help="Decline the case.")] = False,
    api: ApiOption = None,
    token: TokenOption = None,
    as_json: JsonOption = False,
) -> None:
    """Approve or decline a case in human review. You cannot review your own submission.

    Example: mcp-greenroom review 3f2c9a1e-... --approve --note "Read-only, checked."
    """
    if approve == decline:
        raise typer.BadParameter("give exactly one of --approve or --decline.")
    payload = {"action": "approve" if approve else "decline", "note": note}
    path = f"/submissions/{quote(submission_id, safe='')}/review"
    body = _call("POST", path, api, token, as_json, json=payload)
    if not as_json:
        show_decision(body)
    raise typer.Exit(EXIT_OK)


@app.command()
def audit(
    submission_id: IdArgument,
    api: ApiOption = None,
    token: TokenOption = None,
    as_json: JsonOption = False,
) -> None:
    """List the audit records of a submission, oldest first.

    Example: mcp-greenroom audit 3f2c9a1e-...
    """
    path = f"/submissions/{quote(submission_id, safe='')}/audit"
    body = _call("GET", path, api, token, as_json)
    if as_json:
        raise typer.Exit(EXIT_OK)
    out = stdout_console()
    for event in body.get("events") or []:
        fields = ("at", "actor", "action")
        line = Text("  ").join(inert(event.get(key)) for key in fields)
        line.append("  policy ").append(inert(event.get("policy_version")))
        out.print(line)
        for reason in event.get("reasons") or []:
            out.print(Text("    ").append(inert(f"{reason.get('code')}: {reason.get('message')}")))
    next_step(f"{NAME} status {submission_id}")
    raise typer.Exit(EXIT_OK)


@app.command("list")
def list_servers(
    api: ApiOption = None, token: TokenOption = None, as_json: JsonOption = False
) -> None:
    """List the approved versions on the registry, every page.

    Example: mcp-greenroom list
    """
    records: list[dict[str, Any]] = []
    degraded_since: str | None = None
    cursor: str | None = None
    for _ in range(MAX_PAGES):
        response = _send(
            "GET", "/v0.1/servers", api, token, params={"cursor": cursor} if cursor else {}
        )
        body = _json(response)
        records += body.get("servers") or []
        if response.headers.get(DEGRADED_HEADER, "").lower() == "true":
            degraded_since = response.headers.get(GENERATED_AT_HEADER, "an unknown time")
        cursor = (body.get("metadata") or {}).get("nextCursor")
        if not cursor:
            break
    if as_json:  # one ServerList document holding every page
        sys.stdout.write(
            json.dumps({"servers": records, "metadata": {"count": len(records)}}) + "\n"
        )
        raise typer.Exit(EXIT_OK)
    out = stdout_console()
    if degraded_since:
        out.print(
            Text(
                f"! degraded: the registry serves its last-good copy from {degraded_since}.",
                style="yellow",
            )
        )
    for record in records:
        server = record.get("server") or {}
        out.print(
            Text("  ")
            .append(inert(server.get("name")))
            .append(" ")
            .append(inert(server.get("version")))
        )
    out.print(Text(f"{len(records)} approved version(s)."))
    next_step(f"{NAME} client-check CONFIG, to see what a client would allow")
    raise typer.Exit(EXIT_OK)


@app.command()
def health(api: ApiOption = None, token: TokenOption = None) -> None:
    """Show liveness, readiness and registry mode, one line each. Exit 1 unless all are fine.

    Example: mcp-greenroom health
    """
    live = _send("GET", "/livez", api, token).is_success
    ready_response = _send("GET", "/readyz", api, token)
    ready = ready_response.is_success
    listing = _send("GET", "/v0.1/servers", api, token, params={"limit": 1})
    degraded = listing.headers.get(DEGRADED_HEADER, "").lower() == "true"
    out = stdout_console()
    out.print(Text("✓ live", "green") if live else Text("✗ not live", "red"))
    if ready:
        out.print(Text("✓ ready", "green"))
    else:
        reason = error_body(ready_response).get("reason") or f"HTTP {ready_response.status_code}"
        out.print(Text("✗ not ready: ", "red").append(inert(reason)))
    if not listing.is_success:
        out.print(Text(f"✗ registry list failed: HTTP {listing.status_code}", "red"))
    elif degraded:
        since = listing.headers.get(GENERATED_AT_HEADER, "an unknown time")
        out.print(Text("! registry degraded: last-good copy from ", "yellow").append(inert(since)))
    else:
        out.print(Text("✓ registry normal", "green"))
    healthy = live and ready and listing.is_success and not degraded
    next_step(f"{NAME} list" if healthy else "check the API log; 'make run' restarts the service")
    raise typer.Exit(EXIT_OK if healthy else EXIT_FAILURE)


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
        fail(
            "Could not read the client config.",
            f"{config} ({type(exc).__name__})",
            "Pass a JSON file with an 'amp.mcpServers' object.",
            EXIT_FAILURE,
        )
    out = stdout_console()
    out.print(Text("Simulation of Amp's documented registry check, not Amp itself."))
    for verdict in verdicts:
        mark = ("✓ allowed", "green") if verdict.allowed else ("✗ blocked", "red")
        reason = inert(verdict.reason)
        reason.stylize("dim")
        out.print(Text.assemble(mark, "  ", inert(verdict.server), "  ", reason))
    if all(v.allowed for v in verdicts):
        next_step(f"{NAME} list, to see every approved version")
        return
    next_step(f"submit the blocked server with {NAME} submit FILE, or remove it from the config")
    raise typer.Exit(EXIT_REJECTED)
