"""Builders for unit tests: the named samples, and copies with one field changed."""

import json
from pathlib import Path
from typing import Any

from mcp_greenroom.models import Submission, Tool

SAMPLES = Path(__file__).resolve().parents[2] / "sample-data" / "servers"


def load_sample(slug: str) -> Submission:
    return Submission.model_validate_json((SAMPLES / f"{slug}.json").read_text(encoding="utf-8"))


def raw_sample(slug: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((SAMPLES / f"{slug}.json").read_text(encoding="utf-8"))
    return data


def with_server(slug: str = "payments-readonly", **changes: Any) -> Submission:
    """The sample with top-level server.json fields replaced (None removes the field)."""
    data = raw_sample(slug)
    for key, value in changes.items():
        if value is None:
            data["server"].pop(key, None)
        else:
            data["server"][key] = value
    return Submission.model_validate(data)


def with_package(slug: str = "payments-readonly", **changes: Any) -> Submission:
    """The sample with fields of its first package replaced (None removes the field)."""
    data = raw_sample(slug)
    package = data["server"]["packages"][0]
    for key, value in changes.items():
        if value is None:
            package.pop(key, None)
        else:
            package[key] = value
    return Submission.model_validate(data)


def with_tools(tools: list[Tool], slug: str = "payments-readonly") -> Submission:
    return load_sample(slug).model_copy(update={"tools": tools})
