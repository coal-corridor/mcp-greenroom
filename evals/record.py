"""The recording run: one live call per tool, one recording per tool. Only the user starts it,
through /record-classifier (`make record`). It needs MCP_GREENROOM_MODEL and
MCP_GREENROOM_MODEL_API_KEY in the shell, and the network.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from mcp_greenroom.models import Tool
from mcp_greenroom.risk.live import LiveProvider
from mcp_greenroom.risk.prompt import Prompt


@dataclass
class Summary:
    recorded: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    orphans: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    model_ids: set[str] = field(default_factory=set)


def targets() -> list[Tool]:
    raise NotImplementedError


def record_all(
    provider: LiveProvider,
    prompt: Prompt,
    directory: Path,
    tools: list[Tool],
    *,
    force: bool = False,
    prune: bool = False,
    clock: Callable[[], datetime] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> Summary:
    raise NotImplementedError


def main(argv: list[str] | None = None) -> int:
    raise NotImplementedError
