"""The recorder writes one recording per tool, skips unrecorded-reporter, and never the key.

Runs against a mock transport and a temporary directory: never evals/recordings/.
"""

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from evals.cases import load_dataset, load_sample
from evals.record import main, record_all, targets

from mcp_greenroom.models import Tool
from mcp_greenroom.risk.live import LiveProvider
from mcp_greenroom.risk.prompt import load_prompt, recording_key
from mcp_greenroom.risk.replay import ReplayProvider

PROMPT = load_prompt()
KEY = "test-key-not-a-secret"
NOW = datetime(2026, 11, 17, 12, 0, tzinfo=UTC)
TOOLS = [
    Tool(name="get_balance", description="Return the balance."),
    Tool(name="send_report", description="Send a report to a URL you choose."),
]


def model(status: int = 200, fail_first: int = 0) -> Callable[[httpx.Request], httpx.Response]:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        handler.calls = calls["n"]  # type: ignore[attr-defined]
        if calls["n"] <= fail_first:
            return httpx.Response(529, json={"type": "error"})
        sent = json.loads(request.content)["messages"][0]["content"]
        egress = "send_report" in sent
        answer = {
            "score": 0.1 if egress else 0.02,
            "capabilities": ["network_egress"] if egress else [],
            "evidence": "",
            "rationale": "Synthetic.",
        }
        return httpx.Response(
            status,
            json={
                "model": "claude-test-model",
                "content": [{"type": "text", "text": json.dumps(answer)}],
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 700, "output_tokens": 30},
            },
        )

    return handler


def run(tmp_path: Path, handler: Callable, tools: list[Tool] = TOOLS, **kw: object):  # type: ignore[no-untyped-def,type-arg]
    provider = LiveProvider(
        "https://models.example.test",
        "claude-test-model",
        KEY,
        PROMPT,
        transport=httpx.MockTransport(handler),
    )
    return record_all(
        provider, PROMPT, tmp_path, tools, clock=lambda: NOW, sleep=lambda _: None, **kw
    )


def test_each_tool_gets_one_recording_that_replays(tmp_path: Path) -> None:
    summary = run(tmp_path, model())
    assert len(summary.recorded) == 2
    assert (summary.input_tokens, summary.output_tokens) == (1400, 60)
    assert summary.model_ids == {"claude-test-model"}
    replayed = ReplayProvider(tmp_path, PROMPT).classify(TOOLS[1])
    assert replayed.score == 0.1
    assert replayed.model_id == "claude-test-model"


def test_a_recording_carries_model_prompt_tokens_and_time_but_never_the_key(
    tmp_path: Path,
) -> None:
    run(tmp_path, model())
    path = tmp_path / f"{recording_key(PROMPT, TOOLS[0])}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["model_id"] == "claude-test-model"
    assert data["prompt_hash"] == PROMPT.hash
    assert data["prompt_version"] == "classifier-v1"
    assert data["usage"] == {"input_tokens": 700, "output_tokens": 30}
    assert data["recorded_at"].startswith("2026-11-17T12:00")
    assert KEY not in path.read_text(encoding="utf-8")


def test_existing_recordings_are_kept_unless_forced(tmp_path: Path) -> None:
    run(tmp_path, model())
    handler = model()
    assert len(run(tmp_path, handler).skipped) == 2
    assert not hasattr(handler, "calls")
    assert len(run(tmp_path, model(), force=True).recorded) == 2


def test_a_busy_model_is_retried_then_recorded(tmp_path: Path) -> None:
    summary = run(tmp_path, model(fail_first=2), tools=TOOLS[:1])
    assert len(summary.recorded) == 1


def test_a_call_that_keeps_failing_writes_nothing(tmp_path: Path) -> None:
    summary = run(tmp_path, model(status=500), tools=TOOLS[:1])
    assert len(summary.failed) == 1
    assert list(tmp_path.glob("*.json")) == []


def test_recordings_no_target_needs_are_reported_and_pruned_only_on_request(
    tmp_path: Path,
) -> None:
    run(tmp_path, model())
    assert len(run(tmp_path, model(), tools=TOOLS[:1]).orphans) == 1
    assert len(list(tmp_path.glob("*.json"))) == 2
    run(tmp_path, model(), tools=TOOLS[:1], prune=True)
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_the_targets_are_the_set_and_the_samples_except_unrecorded_reporter() -> None:
    names = {tool.name for tool in targets()}
    assert {case.tool.name for case in load_dataset()} <= names
    assert {"search_notes", "sync_notes", "get_balance", "export_report"} <= names
    assert not {t.name for t in load_sample("unrecorded-reporter").tools} & names


def test_without_a_model_or_key_the_run_stops_before_any_call(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import os

    for name in list(os.environ):
        if name.startswith("MCP_GREENROOM_"):
            monkeypatch.delenv(name)
    monkeypatch.chdir(Path(__file__).resolve().parents[2])
    assert main(["--env-file", ""]) == 2
    assert "MCP_GREENROOM_MODEL_API_KEY" in capsys.readouterr().err
