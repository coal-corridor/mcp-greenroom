"""The classifier prompt: a versioned file, its hash, and the replay key for one tool.

The file starts with a "prompt-version: <version>" line. The hash covers the whole file,
so any edit changes it, and with it every replay key: an edited prompt never replays an
answer recorded for another one.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from mcp_greenroom.models import Tool

PROMPT_FILE = Path(__file__).parent / "prompts" / "classifier-v1.md"
_VERSION_PREFIX = "prompt-version:"


@dataclass(frozen=True)
class Prompt:
    version: str
    text: str
    hash: str


def load_prompt(path: Path = PROMPT_FILE) -> Prompt:
    raw = path.read_text(encoding="utf-8")
    first, _, rest = raw.partition("\n")
    if not first.startswith(_VERSION_PREFIX) or not first.removeprefix(_VERSION_PREFIX).strip():
        raise ValueError(
            f"Prompt file has no version: {path} must start with '{_VERSION_PREFIX} <version>'. "
            f"Received first line {ascii(first[:60])}. Add the version line."
        )
    version = first.removeprefix(_VERSION_PREFIX).strip()
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return Prompt(version=version, text=rest.strip(), hash=f"sha256:{digest}")


def user_message(tool: Tool) -> str:
    """The tool as JSON data between tags. Angle brackets are escaped, so the data cannot
    close the tag around it."""
    data = json.dumps({"name": tool.name, "description": tool.description}, ensure_ascii=True)
    data = data.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return f"<tool_definition>\n{data}\n</tool_definition>"


def recording_key(prompt: Prompt, tool: Tool) -> str:
    """Hex sha256 over the prompt version and hash, the tool name and the description."""
    material = json.dumps(
        [prompt.version, prompt.hash, tool.name, tool.description], ensure_ascii=True
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()
