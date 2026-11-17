"""The last-good copy of the published list, read when the database is down."""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


class SnapshotMissing(Exception):  # noqa: N818 (a state, not a bug)
    """No last-good copy has been written yet, or it cannot be read."""


def write_snapshot(path: Path, records: list[dict[str, Any]], generated_at: datetime) -> None:
    """Replace the snapshot atomically: a reader sees the old copy or the new one, never half."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"generated_at": generated_at.isoformat(), "servers": records})
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def read_snapshot(path: Path) -> tuple[list[dict[str, Any]], str]:
    """Return the records and the time they were generated. Raises SnapshotMissing."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return list(data["servers"]), str(data["generated_at"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SnapshotMissing(f"no readable last-good copy at {path}") from exc
