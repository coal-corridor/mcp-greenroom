"""Replay provider: answers from a recording on an exact key match only. The default."""

from pathlib import Path

from mcp_greenroom.models import RiskResult, Tool
from mcp_greenroom.risk.prompt import Prompt, load_prompt


class ReplayProvider:
    """Implements interfaces.ClassifierProvider from evals/recordings/."""

    def __init__(self, recordings_dir: Path, prompt: Prompt | None = None) -> None:
        self.recordings_dir = recordings_dir
        self.prompt = prompt or load_prompt()

    def classify(self, tool: Tool) -> RiskResult:
        raise NotImplementedError
