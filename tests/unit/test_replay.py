"""Replay answers an exact match only. A miss is never guessed (Abstain criterion)."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from mcp_greenroom.interfaces import ClassifierUnavailable, NoRecording
from mcp_greenroom.models import Capability, Tool
from mcp_greenroom.risk.prompt import load_prompt, recording_key
from mcp_greenroom.risk.recording import Recording, Usage, recording_path, write_recording
from mcp_greenroom.risk.replay import ReplayProvider

PROMPT = load_prompt()
TOOL = Tool(name="get_balance", description="Return the balance of one account.")
ANSWER = json.dumps(
    {"score": 0.04, "capabilities": ["local_read"], "evidence": "", "rationale": "Reads."}
)


def record(directory: Path, tool: Tool = TOOL, **changes: object) -> Path:
    fields: dict[str, object] = {
        "key": recording_key(PROMPT, tool),
        "prompt_version": PROMPT.version,
        "prompt_hash": PROMPT.hash,
        "model_id": "model-x",
        "recorded_at": datetime(2026, 11, 17, tzinfo=UTC),
        "tool_name": tool.name,
        "description_sha256": hashlib.sha256(tool.description.encode()).hexdigest(),
        "stop_reason": "end_turn",
        "usage": Usage(input_tokens=900, output_tokens=40),
        "answer": ANSWER,
    }
    fields.update(changes)
    return write_recording(directory, Recording.model_validate(fields))


def test_an_exact_match_replays_the_recorded_answer(tmp_path: Path) -> None:
    record(tmp_path)
    result = ReplayProvider(tmp_path, PROMPT).classify(TOOL)
    assert result.tool_name == "get_balance"
    assert result.score == 0.04
    assert result.capabilities == {Capability.LOCAL_READ}
    assert (result.model_id, result.prompt_hash) == ("model-x", PROMPT.hash)


def test_the_recording_is_written_under_its_key(tmp_path: Path) -> None:
    path = record(tmp_path)
    assert path == recording_path(tmp_path, recording_key(PROMPT, TOOL))
    assert json.loads(path.read_text(encoding="utf-8"))["model_id"] == "model-x"


@pytest.mark.parametrize(
    "asked",
    [
        TOOL.model_copy(update={"description": TOOL.description + " "}),
        TOOL.model_copy(update={"name": "get_balance2"}),
        Tool(name="other", description="Something else."),
    ],
)
def test_a_miss_is_never_guessed(tmp_path: Path, asked: Tool) -> None:
    record(tmp_path)
    with pytest.raises(NoRecording):
        ReplayProvider(tmp_path, PROMPT).classify(asked)


def test_a_missing_directory_is_a_miss(tmp_path: Path) -> None:
    with pytest.raises(NoRecording):
        ReplayProvider(tmp_path / "absent", PROMPT).classify(TOOL)


@pytest.mark.parametrize(
    "changes",
    [
        {"stop_reason": "refusal"},
        {"stop_reason": "max_tokens"},
        {"answer": "not json"},
        {"prompt_hash": "sha256:" + "0" * 64},
        {"tool_name": "someone_else"},
        {"description_sha256": "0" * 64},
    ],
)
def test_a_recording_that_does_not_fit_is_unavailable(tmp_path: Path, changes: dict) -> None:
    record(tmp_path, **changes)
    with pytest.raises(ClassifierUnavailable):
        ReplayProvider(tmp_path, PROMPT).classify(TOOL)


def test_an_unreadable_recording_file_is_unavailable(tmp_path: Path) -> None:
    recording_path(tmp_path, recording_key(PROMPT, TOOL)).write_text("{", encoding="utf-8")
    with pytest.raises(ClassifierUnavailable):
        ReplayProvider(tmp_path, PROMPT).classify(TOOL)
