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


def test_audit_lists_time_actor_action_reasons_and_policy_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event = {
        "submission_id": "sub-1",
        "actor": "dana",
        "action": "submitted",
        "at": "2026-11-17T10:00:00Z",
        "reasons": [],
        "policy_version": "2026-11-17.1",
    }
    decided = {
        **event,
        "actor": "riley",
        "action": "approved",
        "at": "2026-11-17T10:05:00Z",
        "reasons": [{"code": "review.approved", "message": "Note‮[b]x[/b]", "tool_name": None}],
    }
    body = {"submission_id": "sub-1", "events": [event, decided]}

    def route(request: httpx.Request) -> httpx.Response:
        assert (request.method, request.url.path) == ("GET", "/submissions/sub-1/audit")
        return httpx.Response(200, json=body)

    monkeypatch.setattr(cli, "TRANSPORT", api(route))

    result = runner.invoke(app, ["audit", "sub-1", *API])
    as_json = runner.invoke(app, ["audit", "sub-1", *API, "--json"])

    assert result.exit_code == 0, result.output
    for text in ("2026-11-17T10:05:00Z", "riley", "approved", "review.approved", "2026-11-17.1"):
        assert text in result.stdout
    assert "Note\\u202e[b]x[/b]" in result.stdout
    assert json.loads(as_json.stdout) == body


def _listing(degraded: bool) -> httpx.MockTransport:
    pages = {
        None: (
            {"servers": [_server("payments-readonly", "1.2.0")], "metadata": {"nextCursor": "p2"}}
        ),
        "p2": ({"servers": [_server("ambiguous-exporter", "2.0.0")], "metadata": {}}),
    }

    def route(request: httpx.Request) -> httpx.Response:
        assert (request.method, request.url.path) == ("GET", "/v0.1/servers")
        headers = (
            {"X-Greenroom-Degraded": "true", "X-Greenroom-Generated-At": "2026-11-17T09:00:00Z"}
            if degraded
            else {}
        )
        return httpx.Response(200, json=pages[request.url.params.get("cursor")], headers=headers)

    return api(route)


def _server(slug: str, version: str) -> dict[str, object]:
    return {"server": {"name": f"com.examplebank/{slug}", "version": version}}


def test_list_shows_every_approved_version_across_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "TRANSPORT", _listing(degraded=False))

    result = runner.invoke(app, ["list", *API])

    assert result.exit_code == 0, result.output
    assert "com.examplebank/payments-readonly" in result.stdout
    assert "com.examplebank/ambiguous-exporter" in result.stdout
    assert "degraded" not in result.stdout.lower()


def test_list_warns_when_the_registry_is_degraded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "TRANSPORT", _listing(degraded=True))

    result = runner.invoke(app, ["list", *API])

    assert result.exit_code == 0, result.output
    assert "degraded" in result.stdout.lower()
    assert "2026-11-17T09:00:00Z" in result.stdout


def _health(ready: bool) -> httpx.MockTransport:
    def route(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/livez":
            return httpx.Response(200, json={"alive": True})
        if path == "/readyz" and ready:
            return httpx.Response(200, json={"ready": True})
        if path == "/readyz":
            return httpx.Response(503, json={"ready": False, "reason": "store unavailable: disk"})
        assert path == "/v0.1/servers"
        headers = {} if ready else {"X-Greenroom-Degraded": "true"}
        return httpx.Response(200, json={"servers": []}, headers=headers)

    return api(route)


def test_health_prints_liveness_readiness_and_registry_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "TRANSPORT", _health(ready=True))

    result = runner.invoke(app, ["health", *API])

    assert result.exit_code == 0, result.output
    lines = [line for line in result.stdout.splitlines() if not line.startswith("Next:")]
    assert len(lines) == 3
    assert "✓ live" in lines[0]
    assert "✓ ready" in lines[1]
    assert "normal" in lines[2]


def test_health_exits_1_and_says_why_when_not_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "TRANSPORT", _health(ready=False))

    result = runner.invoke(app, ["health", *API])

    assert result.exit_code == 1
    assert "store unavailable: disk" in result.stdout
    assert "degraded" in result.stdout
