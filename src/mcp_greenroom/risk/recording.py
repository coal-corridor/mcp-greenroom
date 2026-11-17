"""One recorded classifier exchange per tool, as a JSON file named by its replay key.

Written only by the recorder (evals/record.py, `make record`). Never by hand.
"""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class Usage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    input_tokens: int = 0
    output_tokens: int = 0


class Recording(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    format: int = 1
    key: str
    prompt_version: str
    prompt_hash: str
    model_id: str
    recorded_at: datetime
    tool_name: str
    description_sha256: str
    stop_reason: str
    usage: Usage
    answer: str


def recording_path(directory: Path, key: str) -> Path:
    return directory / f"{key}.json"


def write_recording(directory: Path, recording: Recording) -> Path:
    raise NotImplementedError
