"""Output for the mcp-greenroom command: status words, exit codes, errors, inert text.

Untrusted text (tool names, descriptions, evidence, notes) goes through inert() only.
"""

import unicodedata
from typing import Any, NoReturn

import httpx
import typer
from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text
from typer.core import TyperGroup
from typer.exceptions import TyperException

NAME = "mcp-greenroom"

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_REVIEW = 10
EXIT_REJECTED = 20

# Outcome -> (symbol and word, colour that only repeats it, exit code).
OUTCOMES = {
    "approved": ("✓ approved", "green", EXIT_OK),
    "human_review": ("! needs review", "yellow", EXIT_REVIEW),
    "rejected": ("✗ rejected", "red", EXIT_REJECTED),
}


def stdout_console() -> Console:
    return Console(highlight=False, soft_wrap=True)


def stderr_console() -> Console:
    return Console(stderr=True, highlight=False, soft_wrap=True)


def fail(what: str, received: str, todo: str, code: int = EXIT_FAILURE) -> NoReturn:
    """Print a three-part error to standard error and exit. What and received may carry
    text from the API or a file, so both are printed inert."""
    err = stderr_console()
    err.print(Text.assemble(("Error: ", "bold red"), inert(what)))
    err.print(Text("  Received: ").append(inert(received)))
    err.print(Text(f"  Next: {todo}"))
    raise typer.Exit(code)


def next_step(step: str) -> None:
    stdout_console().print(Text(f"Next: {step}", style="dim"))


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


def show_findings(out: Console, findings: list[dict[str, Any]]) -> None:
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


def exit_code(body: dict[str, Any]) -> int:
    return OUTCOMES.get(str(body.get("outcome")), ("", "", EXIT_FAILURE))[2]


def show_decision(body: dict[str, Any]) -> int:
    """Print a submission's decision. Returns the exit code for its outcome."""
    word, colour, code = OUTCOMES.get(str(body.get("outcome")), ("? unknown", "", EXIT_FAILURE))
    tier = body.get("tier") or "none"
    out = stdout_console()
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
        show_findings(out, findings)
    next_step(f"{NAME} status {body.get('submission_id')}")
    return code


def error_body(response: httpx.Response) -> dict[str, Any]:
    """The API's error body: rule_id and message at the top level (or under FastAPI's detail)."""
    try:
        body = response.json()
    except ValueError:
        return {}
    if isinstance(body, dict) and isinstance(body.get("detail"), dict):
        body = body["detail"]
    return body if isinstance(body, dict) else {}


def fail_from(response: httpx.Response) -> NoReturn:
    status = response.status_code
    body = error_body(response)
    rule, message = body.get("rule_id"), body.get("message")
    what = f"HTTP {status}" + (f" [{rule}]" if rule else "") + (f": {message}" if message else "")
    received = str(body["received"]) if body.get("received") else None
    if status == 401:
        fail(
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
        fail(what, received or f"refused by the API ({status})", todo, EXIT_REJECTED)
    fail(what, received or f"HTTP {status} from the API", "Check the API log, then try again.")


class GuardedGroup(TyperGroup):
    """Turns an unexpected exception into a three-part error, unless --debug was given."""

    def invoke(self, ctx: Any) -> Any:  # Typer keeps its Context type private
        try:
            return super().invoke(ctx)
        except (typer.Exit, typer.Abort, TyperException):
            raise
        except Exception as exc:
            if ctx.params.get("debug"):
                raise
            fail(
                "mcp-greenroom stopped on an unexpected error.",
                type(exc).__name__,
                "Run the same command with --debug before it to see the stack trace.",
            )
