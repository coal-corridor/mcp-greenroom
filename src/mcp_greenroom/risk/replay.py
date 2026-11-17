"""Replay provider: answers from a recording on an exact key match only. The default.

A missing recording is NoRecording. A recording that exists but does not fit the tool,
the prompt or a clean end of turn is ClassifierUnavailable. Neither is ever guessed.
"""

from pathlib import Path

from pydantic import ValidationError

from mcp_greenroom.interfaces import ClassifierUnavailable, NoRecording
from mcp_greenroom.models import RiskResult, Tool
from mcp_greenroom.risk.parse import parse_answer
from mcp_greenroom.risk.prompt import Prompt, load_prompt, recording_key
from mcp_greenroom.risk.recording import Recording, description_digest, recording_path


class ReplayProvider:
    """Implements interfaces.ClassifierProvider from evals/recordings/."""

    def __init__(self, recordings_dir: Path, prompt: Prompt | None = None) -> None:
        self.recordings_dir = recordings_dir
        self.prompt = prompt or load_prompt()

    def classify(self, tool: Tool) -> RiskResult:
        key = recording_key(self.prompt, tool)
        path = recording_path(self.recordings_dir, key)
        if not path.is_file():
            raise NoRecording(
                f"No recording for this tool under prompt {self.prompt.version}: "
                f"key {key[:12]} not found in {self.recordings_dir}. "
                "A miss is never guessed; the tool goes to human review."
            )
        try:
            recording = Recording.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValidationError):
            raise ClassifierUnavailable(
                f"Recording unreadable: {path.name}. Regenerate it with /record-classifier."
            ) from None
        fits = (
            recording.key == key
            and recording.prompt_hash == self.prompt.hash
            and recording.tool_name == tool.name
            and recording.description_sha256 == description_digest(tool.description)
        )
        if not fits:
            raise ClassifierUnavailable(
                f"Recording does not fit the tool or prompt: {path.name}. "
                "Regenerate it with /record-classifier."
            )
        if recording.stop_reason != "end_turn":
            raise ClassifierUnavailable(
                f"Recorded answer did not end cleanly: stop reason "
                f"{ascii(recording.stop_reason[:20])}. The tool goes to human review."
            )
        return parse_answer(recording.answer, tool.name, recording.model_id, self.prompt.hash)
