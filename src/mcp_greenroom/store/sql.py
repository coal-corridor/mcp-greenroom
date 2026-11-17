"""The store: SQLAlchemy 2 (sync) on SQLite.

Every database error becomes StoreUnavailable, so the API can degrade instead of crashing.
A fresh connection per operation (NullPool) means a broken database file shows up at once.
"""

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Connection, create_engine, func, insert, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.pool import NullPool

from mcp_greenroom.logging import log_event
from mcp_greenroom.models import AuditEvent, Decision, Outcome, Submission
from mcp_greenroom.store.snapshot import write_snapshot
from mcp_greenroom.store.tables import (
    append_only_triggers,
    audit_events,
    decisions,
    metadata,
    published,
    submissions,
)

OFFICIAL_META = "io.modelcontextprotocol.registry/official"


class StoreUnavailable(Exception):  # noqa: N818 (a state the API degrades on)
    """The database could not be reached or answered with an error."""


class VersionTaken(Exception):  # noqa: N818
    """Another submission already holds this name and version."""


class NotPending(Exception):  # noqa: N818
    """The submission is not waiting for a human decision."""


@dataclass(frozen=True)
class StoredSubmission:
    id: str
    name: str
    version: str
    fingerprint: str
    submitted_by: str
    decision: Decision  # the current one: the human decision once made, else the policy one


class SqlStore:
    """Persistence for submissions, decisions, the published list and the audit trail.

    There is no method that updates or deletes an audit event, and the tables refuse both.
    """

    def __init__(self, database_url: str, snapshot_path: Path) -> None:
        self._engine = create_engine(database_url, poolclass=NullPool)
        self._snapshot_path = snapshot_path

    @contextmanager
    def _tx(self) -> Iterator[Connection]:
        try:
            with self._engine.begin() as conn:
                yield conn
        except (IntegrityError, VersionTaken, NotPending):
            raise
        except SQLAlchemyError as exc:
            raise StoreUnavailable(f"database error: {type(exc).__name__}") from exc

    def ensure_schema(self) -> None:
        with self._tx() as conn:
            metadata.create_all(conn)
            for trigger in append_only_triggers():
                conn.execute(text(trigger))

    def ping(self) -> None:
        """Raise StoreUnavailable unless the database answers a query on its own tables."""
        with self._tx() as conn:
            conn.execute(select(func.count()).select_from(submissions))
            conn.execute(text("PRAGMA quick_check"))

    # Reads

    def _current(self, conn: Connection, submission_id: str) -> Decision:
        row = conn.execute(
            select(decisions.c.decision_json)
            .where(decisions.c.submission_id == submission_id)
            .order_by(decisions.c.seq.desc())
            .limit(1)
        ).one()
        return Decision.model_validate_json(row.decision_json)

    def _stored(self, conn: Connection, row: Any) -> StoredSubmission:
        return StoredSubmission(
            id=row.id,
            name=row.name,
            version=row.version,
            fingerprint=row.fingerprint,
            submitted_by=row.submitted_by,
            decision=self._current(conn, row.id),
        )

    def get(self, submission_id: str) -> StoredSubmission | None:
        with self._tx() as conn:
            row = conn.execute(select(submissions).where(submissions.c.id == submission_id)).first()
            return self._stored(conn, row) if row else None

    def find(self, name: str, version: str) -> StoredSubmission | None:
        with self._tx() as conn:
            row = conn.execute(
                select(submissions).where(
                    submissions.c.name == name, submissions.c.version == version
                )
            ).first()
            return self._stored(conn, row) if row else None

    def audit(self, submission_id: str) -> list[AuditEvent]:
        with self._tx() as conn:
            rows = conn.execute(
                select(audit_events.c.event_json)
                .where(audit_events.c.submission_id == submission_id)
                .order_by(audit_events.c.id)
            )
            return [AuditEvent.model_validate_json(row.event_json) for row in rows]

    def published(self) -> list[dict[str, Any]]:
        """Every published version as an upstream ServerResponse, by name then version."""
        with self._tx() as conn:
            rows = conn.execute(
                select(published).order_by(published.c.name, published.c.version)
            ).all()
        return [
            {
                "server": json.loads(row.server_json),
                "_meta": {
                    OFFICIAL_META: {
                        "status": "active",
                        "publishedAt": row.published_at,
                        "updatedAt": row.published_at,
                    }
                },
            }
            for row in rows
        ]

    # Writes

    def append_audit(self, event: AuditEvent) -> None:
        with self._tx() as conn:
            self._audit(conn, event)

    def _audit(self, conn: Connection, event: AuditEvent) -> None:
        conn.execute(
            insert(audit_events).values(
                submission_id=event.submission_id, event_json=event.model_dump_json()
            )
        )

    def _publish(self, conn: Connection, submission_id: str) -> None:
        row = conn.execute(select(submissions).where(submissions.c.id == submission_id)).one()
        conn.execute(
            insert(published).values(
                submission_id=row.id,
                name=row.name,
                version=row.version,
                server_json=row.server_json,
                published_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            )
        )

    def create(
        self,
        submission_id: str,
        submission: Submission,
        fingerprint: str,
        submitted_by: str,
        decision: Decision,
        events: list[AuditEvent],
    ) -> None:
        """Store a new submission with its policy decision. Publishes it if approved.

        Raises VersionTaken when the name and version are already held.
        """
        try:
            with self._tx() as conn:
                conn.execute(
                    insert(submissions).values(
                        id=submission_id,
                        name=submission.name,
                        version=submission.version,
                        fingerprint=fingerprint,
                        submitted_by=submitted_by,
                        server_json=json.dumps(submission.server, sort_keys=True),
                        created_at=datetime.now(UTC).isoformat(),
                    )
                )
                self._decide(conn, submission_id, 0, decision, events)
        except IntegrityError as exc:
            raise VersionTaken(f"{submission.name} {submission.version}") from exc
        self._after_decision(decision)

    def decide(self, submission_id: str, decision: Decision, event: AuditEvent) -> None:
        """Add the human decision to a submission in human review. Raises NotPending."""
        try:
            with self._tx() as conn:
                if self._current(conn, submission_id).outcome != Outcome.HUMAN_REVIEW:
                    raise NotPending(submission_id)
                self._decide(conn, submission_id, 1, decision, [event])
        except IntegrityError as exc:  # a concurrent review took seq 1 first
            raise NotPending(submission_id) from exc
        self._after_decision(decision)

    def _decide(
        self,
        conn: Connection,
        submission_id: str,
        seq: int,
        decision: Decision,
        events: list[AuditEvent],
    ) -> None:
        conn.execute(
            insert(decisions).values(
                submission_id=submission_id, seq=seq, decision_json=decision.model_dump_json()
            )
        )
        for event in events:
            self._audit(conn, event)
        if decision.outcome == Outcome.APPROVED:
            self._publish(conn, submission_id)

    def _after_decision(self, decision: Decision) -> None:
        if decision.outcome == Outcome.APPROVED:
            self.refresh_snapshot()

    def refresh_snapshot(self) -> None:
        """Write the last-good copy. A failure is logged: the publish itself stands."""
        try:
            write_snapshot(self._snapshot_path, self.published(), datetime.now(UTC))
        except (OSError, StoreUnavailable) as exc:
            log_event("snapshot.write_failed", logging.ERROR, error=type(exc).__name__)
