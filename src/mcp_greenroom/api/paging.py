"""Cursor paging over the published list, the same for the database and the last-good copy."""

import base64
import json
from typing import Any

DEFAULT_LIMIT = 30
MAX_LIMIT = 100


def encode_cursor(name: str, version: str) -> str:
    raw = json.dumps([name, version], separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[str, str] | None:
    """Return the (name, version) after which the page starts, or None if unreadable."""
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        name, version = json.loads(base64.urlsafe_b64decode(padded.encode()))
    except (ValueError, TypeError):
        return None
    if not isinstance(name, str) or not isinstance(version, str):
        return None
    return name, version


def page(
    records: list[dict[str, Any]], after: tuple[str, str] | None, limit: int
) -> dict[str, Any]:
    """One page of an upstream ServerList. Records are sorted by name, then version (text)."""

    def key(record: dict[str, Any]) -> tuple[str, str]:
        return str(record["server"]["name"]), str(record["server"]["version"])

    remaining = [r for r in sorted(records, key=key) if after is None or key(r) > after]
    items = remaining[:limit]
    metadata: dict[str, Any] = {"count": len(items)}
    if len(remaining) > limit:
        metadata["nextCursor"] = encode_cursor(*key(items[-1]))
    return {"servers": items, "metadata": metadata}
