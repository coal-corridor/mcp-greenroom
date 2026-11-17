"""Decision order step 1: refuse a malformed submission with 422 (interfaces.Refusal).

Every refusal carries a stable rule id and a message in three parts: what failed, what
was received (escaped, truncated), what to do. The received value is untrusted text.
"""

import json
import re
from functools import cache
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema.exceptions import best_match

from mcp_greenroom.interfaces import Refusal
from mcp_greenroom.models import Submission

MAX_RECEIVED = 80
SCHEMA_PATH = Path(__file__).resolve().parents[3] / "contracts" / "server.schema.json"

# One exact version: digits first (an optional "v"), dot-separated numbers, then an optional
# pre-release or build suffix. Refuses tags ("latest", "next"), ranges and wildcards.
_PINNED = re.compile(r"v?\d+(?:\.\d+)*(?:[-+][0-9A-Za-z.+-]+)?")


def escaped(value: object) -> str:
    """Untrusted value as a short, ASCII-only, quoted string."""
    text = value if isinstance(value, str) else repr(value)
    if len(text) > MAX_RECEIVED:
        text = text[:MAX_RECEIVED] + "..."
    return ascii(text)


def _refuse(rule_id: str, failed: str, value: object, todo: str) -> Refusal:
    received = escaped(value)
    return Refusal(rule_id, f"{failed}. Received {received}. {todo}", received)


def is_pinned(version: str) -> bool:
    return _PINNED.fullmatch(version) is not None


def _check_versions(server: dict[str, Any]) -> None:
    versions = [("version", server.get("version"))]
    packages = server.get("packages")
    if isinstance(packages, list):
        versions += [
            (f"packages[{i}].version", package.get("version"))
            for i, package in enumerate(packages)
            if isinstance(package, dict)
        ]
    for where, version in versions:
        if isinstance(version, str) and not is_pinned(version):
            raise _refuse(
                "validation.version_not_pinned",
                f"Version is not pinned: {where} must be one exact version",
                version,
                "Submit an exact version such as 1.2.0: no tag, range or wildcard.",
            )


@cache
def _schema_validator() -> jsonschema.Draft7Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return jsonschema.Draft7Validator(schema)


def _check_schema(server: dict[str, Any]) -> None:
    error = best_match(_schema_validator().iter_errors(server))
    if error is None:
        return
    where = "/" + "/".join(str(part) for part in error.absolute_path)
    raise _refuse(
        "validation.schema",
        f"Server manifest does not fit the schema at {where}: the '{error.validator}' rule failed",
        error.instance,
        "Fix server.json against contracts/server.schema.json (2025-12-11) and submit again.",
    )


def validate(submission: Submission) -> None:
    """Raise Refusal when the submission breaks a step-1 rule. Return None when it passes."""
    _check_versions(submission.server)
    _check_schema(submission.server)
