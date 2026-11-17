"""The mcp-greenroom command. Talks to the API over HTTP only."""

import json
import sys
import unicodedata
from pathlib import Path
from typing import Annotated, Any, NoReturn
from urllib.parse import quote

import httpx
import typer
from rich import box
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

# Outcome -> (symbol and word, colour that only repeats it, exit code).
OUTCOMES = {
    "approved": ("✓ approved", "green", EXIT_OK),
    "human_review": ("! needs review", "yellow", EXIT_REVIEW),
    "rejected": ("✗ rejected", "red", EXIT_REJECTED),
}
TIMEOUT_SECONDS = 10.0

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


# Control, format (zero-width, bidi), private, surrogate, unassigned, line and paragraph separators.
_HIDDEN_CATEGORIES = frozenset({"Cc", "Cf", "Co", "Cs", "Cn", "Zl", "Zp"})


def _escape_char(char: str) -> str:
    point = ord(char)
    if point < 0x100:
        return f"\\x{point:02x}"
    if point < 0x10000:
        return f"\\u{point:04x}"
    return f"\\U{point:08x}"


def inert(value: object) -> Text:
    """Untrusted text, safe to print: no markup is read, hidden characters are shown escaped."""
    shown = "".join(
        _escape_char(c) if unicodedata.category(c) in _HIDDEN_CATEGORIES else c for c in str(value)
    )
    return Text(shown)


def _show_findings(out: Console, findings: list[dict[str, Any]]) -> None:
    """A table of findings, then each finding's offending text on its own unwrapped line."""
    table = Table(box=box.SIMPLE, show_edge=False, pad_edge=False)
    for column in ("#", "rule", "source", "severity", "tool"):
        table.add_column(column, overflow="fold")
    for number, finding in enumerate(findings, start=1):
        cells = (finding.get(key) or "" for key in ("rule_id", "source", "severity", "tool_name"))
        table.add_row(str(number), *(inert(cell) for cell in cells))
    out.print(table)
    for number, finding in enumerate(findings, start=1):
        if finding.get("evidence"):
            out.print(Text(f"  [{number}] offending text: ").append(inert(finding["evidence"])))


def _exit_code(body: dict[str, Any]) -> int:
    return OUTCOMES.get(str(body.get("outcome")), ("", "", EXIT_FAILURE))[2]


def _show_decision(body: dict[str, Any]) -> int:
    """Print a submission's decision. Returns the exit code for its outcome."""
    word, colour, code = OUTCOMES.get(str(body.get("outcome")), ("? unknown", "", EXIT_FAILURE))
    tier = body.get("tier") or "none"
    out = _out()
    name = inert(f"{body.get('name')} {body.get('version')}")
    out.print(Text.assemble((word, colour), "  ", name, f"  tier {inert(tier)}"))
    for reason in body.get("reasons") or []:
        line = Text("  ").append(inert(reason.get("code"))).append(": ")
        line.append(inert(reason.get("message")))
        if reason.get("tool_name"):
            line.append(" (tool ").append(inert(reason["tool_name"])).append(")")
        out.print(line)
    findings = body.get("findings") or []
    if findings:
        _show_findings(out, findings)
    _next(f"{NAME} status {body.get('submission_id')}")
    return code


def _call(
    method: str, path: str, api: str | None, token: str | None, as_json: bool, **kwargs: Any
) -> Any:
    """Send one request. Returns the JSON body of a 2xx answer, or exits with a clear error.

    With as_json, the body is also printed unchanged, alone on standard output.
    """
    with _client(api, token) as client:
        try:
            response = client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            _fail(
                f"The API is unreachable ({type(exc).__name__}).",
                f"{method} {client.base_url.join(path)}",
                "Start it with 'make run', or pass the right address with --api.",
            )
    if as_json and response.content:
        sys.stdout.write(response.text.rstrip("\n") + "\n")
    if not response.is_success:
        _fail_from(response)
    try:
        return response.json()
    except ValueError:
        _fail("The API answer is not JSON.", f"HTTP {response.status_code}", "Check --api.")


def _error_body(response: httpx.Response) -> dict[str, Any]:
    """The API's error body: rule_id and message at the top level (or under FastAPI's detail)."""
    try:
        body = response.json()
    except ValueError:
        return {}
    if isinstance(body, dict) and isinstance(body.get("detail"), dict):
        body = body["detail"]
    return body if isinstance(body, dict) else {}


def _fail_from(response: httpx.Response) -> NoReturn:
    status = response.status_code
    body = _error_body(response)
    rule, message = body.get("rule_id"), body.get("message")
    what = f"HTTP {status}" + (f" [{rule}]" if rule else "") + (f": {message}" if message else "")
    received = str(body["received"]) if body.get("received") else None
    if status == 401:
        _fail(
            what,
            received or "a missing or unknown token",
            "Pass --token, or set MCP_GREENROOM_TOKEN.",
        )
    if status in (403, 409, 422):
        todo = {
            403: "Ask a different reviewer: a reviewer is never the submitter.",
            409: "This name and version is already decided. Submit a new version.",
            422: "Fix the request as the message says, then send it again.",
        }[status]
        _fail(what, received or f"refused by the API ({status})", todo, EXIT_REJECTED)
    _fail(what, received or f"HTTP {status} from the API", "Check the API log, then try again.")


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
        _fail(
            "Could not read the submission file.",
            f"{file} ({type(exc).__name__})",
            "Pass a JSON file with 'server' and 'tools'.",
        )
    body = _call("POST", "/submissions", api, token, as_json, json=payload)
    raise typer.Exit(_exit_code(body) if as_json else _show_decision(body))


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
    raise typer.Exit(_exit_code(body) if as_json else _show_decision(body))


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
