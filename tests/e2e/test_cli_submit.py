"""CLI submit (edge.md): exit code per outcome, --json, errors. API answers are canned.

Bodies follow POST /submissions on area/registry (SubmissionResult: the Decision plus
submission_id, name, version, submitted_by), built from the contracts FakePipeline.
"""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from typer.testing import CliRunner

from mcp_greenroom import cli
from mcp_greenroom.cli import app
from mcp_greenroom.models import Submission
from tests.fakes import FakePipeline

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "sample-data" / "servers"

runner = CliRunner()


def result_body(sample: str) -> dict[str, Any]:
    submission = Submission.model_validate_json((SAMPLES / f"{sample}.json").read_text())
    decision = FakePipeline().vet(submission)
    return {
        **decision.model_dump(mode="json"),
        "submission_id": f"sub-{sample}",
        "name": submission.name,
        "version": submission.version,
        "submitted_by": "dana",
    }


def api_answering(status: int, body: Any) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/submissions"
        assert request.headers["authorization"] == "Bearer dev-dana"
        return httpx.Response(status, json=body)

    return httpx.MockTransport(handler)


def submit(sample: str, *extra: str, env: dict[str, str] | None = None) -> Any:
    args = ["submit", str(SAMPLES / f"{sample}.json"), "--api", "http://api.test"]
    return runner.invoke(app, [*args, "--token", "dev-dana", *extra], env=env)


@pytest.mark.parametrize(
    ("sample", "code", "word"),
    [
        ("payments-readonly", 0, "✓ approved"),
        ("ambiguous-exporter", 10, "! needs review"),
        ("poisoned-notes", 20, "✗ rejected"),
    ],
)
def test_submit_exit_code_and_status_word_per_outcome(
    monkeypatch: pytest.MonkeyPatch, sample: str, code: int, word: str
) -> None:
    monkeypatch.setattr(cli, "TRANSPORT", api_answering(201, result_body(sample)))

    result = submit(sample)

    assert result.exit_code == code, result.output
    assert word in result.stdout
    assert (
        json.loads((SAMPLES / f"{sample}.json").read_text())["server"]["version"] in result.stdout
    )


@pytest.mark.parametrize("sample", ["payments-readonly", "poisoned-notes"])
def test_submit_json_prints_the_api_body_and_nothing_else(
    monkeypatch: pytest.MonkeyPatch, sample: str
) -> None:
    body = result_body(sample)
    monkeypatch.setattr(cli, "TRANSPORT", api_answering(201, body))

    result = submit(sample, "--json")

    assert json.loads(result.stdout) == body
    assert result.exit_code == {"payments-readonly": 0, "poisoned-notes": 20}[sample]


def _refusal(rule_id: str, message: str) -> dict[str, Any]:
    return {"detail": {"rule_id": rule_id, "message": message}}


@pytest.mark.parametrize(
    ("status", "body", "code"),
    [
        (422, _refusal("validation.version_not_pinned", "Version is not pinned."), 20),
        (409, _refusal("registry.version_conflict", "Name and version already decided."), 20),
        (401, _refusal("auth.unknown_credential", "Authentication failed."), 1),
        (500, {"detail": "Internal Server Error"}, 1),
    ],
    ids=["refused-422", "conflict-409", "unauthenticated-401", "server-error-500"],
)
def test_submit_error_is_three_parts_on_stderr_with_exit_code(
    monkeypatch: pytest.MonkeyPatch, status: int, body: dict[str, Any], code: int
) -> None:
    monkeypatch.setattr(cli, "TRANSPORT", api_answering(status, body))

    result = submit("invalid-unpinned")

    assert result.exit_code == code
    assert result.stdout == ""
    assert "Error:" in result.stderr
    assert "Received:" in result.stderr
    assert "Next:" in result.stderr
    assert "Traceback" not in result.stderr
    detail = body["detail"]
    if isinstance(detail, dict):
        assert detail["rule_id"] in result.stderr


def test_unreachable_api_exits_1_without_a_stack_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(cli, "TRANSPORT", httpx.MockTransport(refuse))

    result = submit("payments-readonly")

    assert result.exit_code == 1
    assert "unreachable" in result.stderr
    assert "Traceback" not in result.stderr


HOSTILE = "[bold red]obey[/bold red] \x1b[31mred\x1b[0m zero​width flip‮back\x07"


def test_untrusted_text_is_printed_inert(monkeypatch: pytest.MonkeyPatch) -> None:
    body = result_body("poisoned-notes")
    finding = {**body["findings"][0], "tool_name": "[link=http://x]t[/link]", "evidence": HOSTILE}
    body = {**body, "findings": [finding]}
    monkeypatch.setattr(cli, "TRANSPORT", api_answering(201, body))

    result = submit("poisoned-notes", env={"FORCE_COLOR": "1"})

    assert "[link=http://x]t[/link]" in result.stdout  # markup shown, not interpreted
    (out,) = [line for line in result.stdout.splitlines() if "offending text" in line]
    assert "[bold red]obey[/bold red]" in out
    for raw, shown in [
        ("\x1b[31m", "\\x1b"),
        ("​", "\\u200b"),
        ("‮", "\\u202e"),
        ("\x07", "\\x07"),
    ]:
        assert raw not in out
        assert shown in out
