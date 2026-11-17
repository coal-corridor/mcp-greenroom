"""Client simulator: a simulation of Amp's documented registry check, not Amp itself."""

from dataclasses import dataclass
from pathlib import Path

import httpx


@dataclass(frozen=True)
class Verdict:
    server: str
    allowed: bool
    reason: str


def check_config(config_path: Path, registry: httpx.Client) -> list[Verdict]:
    return []
