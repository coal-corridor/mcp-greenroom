"""Decision order step 1: refuse a malformed submission with 422 (interfaces.Refusal).

Every refusal carries a stable rule id and a message in three parts: what failed, what
was received (escaped, truncated), what to do. The received value is untrusted text.
"""

import re
from typing import Any

from mcp_greenroom.interfaces import Refusal
from mcp_greenroom.models import Submission

MAX_RECEIVED = 80

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


def validate(submission: Submission) -> None:
    """Raise Refusal when the submission breaks a step-1 rule. Return None when it passes."""
    _check_versions(submission.server)
