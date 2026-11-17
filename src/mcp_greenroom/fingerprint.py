"""Fingerprint of one submission: the manifest and the tool definitions."""

import hashlib
import json
from typing import Any

from mcp_greenroom.models import Submission


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fingerprint(submission: Submission) -> str:
    """Return "sha256:<hex>" over canonical JSON of the server.json and the tools.

    Stable under key order and tool order. Any change to the manifest or to a tool
    name, description or input schema changes it.
    """
    tools = sorted(_canonical(tool.model_dump(by_alias=True)) for tool in submission.tools)
    payload = _canonical({"server": submission.server, "tools": tools})
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()
