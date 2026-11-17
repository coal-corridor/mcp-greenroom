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


def _reviewed(outcome: str) -> dict[str, object]:
    body = result_body("ambiguous-exporter")
    reason = {"code": f"review.{outcome}", "message": "Checked.", "tool_name": None}
    return {**body, "outcome": outcome, "decided_by": "riley", "reasons": [reason]}


@pytest.mark.parametrize(
    ("flag", "action", "outcome", "word"),
    [
        ("--approve", "approve", "approved", "✓ approved"),
        ("--decline", "decline", "rejected", "✗ rejected"),
    ],
)
def test_review_records_the_decision_and_exits_0(
    monkeypatch: pytest.MonkeyPatch, flag: str, action: str, outcome: str, word: str
) -> None:
    sent: list[dict[str, str]] = []

    def route(request: httpx.Request) -> httpx.Response:
        assert (request.method, request.url.path) == ("POST", "/submissions/sub-1/review")
        sent.append(json.loads(request.content))
        return httpx.Response(200, json=_reviewed(outcome))

    monkeypatch.setattr(cli, "TRANSPORT", api(route))

    result = runner.invoke(app, ["review", "sub-1", flag, "--note", "Checked.", *API])

    assert result.exit_code == 0, result.output
    assert sent == [{"action": action, "note": "Checked."}]
    assert word in result.stdout


def test_review_by_the_submitter_is_refused_with_exit_20(monkeypatch: pytest.MonkeyPatch) -> None:
    refusal = {"rule_id": "review.reviewer_is_submitter", "message": "Review refused."}
    monkeypatch.setattr(cli, "TRANSPORT", api(lambda _: httpx.Response(403, json=refusal)))

    result = runner.invoke(app, ["review", "sub-1", "--approve", "--note", "Fine.", *API])

    assert result.exit_code == 20
    assert "review.reviewer_is_submitter" in result.stderr


@pytest.mark.parametrize("flags", [[], ["--approve", "--decline"]], ids=["neither", "both"])
def test_review_needs_exactly_one_of_approve_or_decline(flags: list[str]) -> None:
    result = runner.invoke(app, ["review", "sub-1", *flags, "--note", "x", *API])

    assert result.exit_code == 2
