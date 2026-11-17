"""The one logger. Each call writes one structured JSON line.

Tool names, descriptions, evidence and notes are untrusted: they are logged as a
hash and a length, never as text.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

LOGGER_NAME = "mcp_greenroom"

UNTRUSTED_FIELDS = frozenset(
    {"name", "tool_name", "description", "evidence", "note", "text", "notes"}
)

_logger = logging.getLogger(LOGGER_NAME)


def configure_logging(level: str = "INFO") -> None:
    """Send the log lines to stderr. Safe to call more than once."""
    if not any(getattr(h, "_greenroom", False) for h in _logger.handlers):
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(message)s"))
        handler._greenroom = True  # type: ignore[attr-defined]
        _logger.addHandler(handler)
    _logger.setLevel(level)


def log_event(event: str, level: int = logging.INFO, **fields: Any) -> None:
    """Write one JSON line: time, level, event and the given fields."""
    record = {
        "ts": datetime.now(UTC).isoformat(),
        "level": logging.getLevelName(level),
        "event": event,
        **fields,
    }
    _logger.log(level, json.dumps(record, default=str, sort_keys=True))
