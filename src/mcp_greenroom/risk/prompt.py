"""The classifier prompt: a versioned file, its hash, and the replay key for one tool."""

from dataclasses import dataclass
from pathlib import Path

from mcp_greenroom.models import Tool

PROMPT_FILE = Path(__file__).parent / "prompts" / "classifier-v1.md"


@dataclass(frozen=True)
class Prompt:
    version: str
    text: str
    hash: str


def load_prompt(path: Path = PROMPT_FILE) -> Prompt:
    return Prompt(version="", text="", hash="")


def user_message(tool: Tool) -> str:
    return ""


def recording_key(prompt: Prompt, tool: Tool) -> str:
    return ""
