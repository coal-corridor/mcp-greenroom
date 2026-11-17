"""SQLite tables. Audit events and decisions are append-only: triggers refuse UPDATE and DELETE."""

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)

metadata = MetaData()

submissions = Table(
    "submissions",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("name", String(200), nullable=False),
    Column("version", String(255), nullable=False),
    Column("fingerprint", String(80), nullable=False),
    Column("submitted_by", String(100), nullable=False),
    Column("server_json", Text, nullable=False),
    Column("created_at", String(40), nullable=False),
    UniqueConstraint("name", "version", name="uq_submission_name_version"),
)

decisions = Table(
    "decisions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("submission_id", String(36), ForeignKey("submissions.id"), nullable=False),
    Column("seq", Integer, nullable=False),  # 0 is the policy decision, 1 the human one
    Column("decision_json", Text, nullable=False),
    UniqueConstraint("submission_id", "seq", name="uq_decision_seq"),
)

audit_events = Table(
    "audit_events",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("submission_id", String(36), nullable=False, index=True),
    Column("event_json", Text, nullable=False),
)

published = Table(
    "published",
    metadata,
    Column("submission_id", String(36), ForeignKey("submissions.id"), primary_key=True),
    Column("name", String(200), nullable=False),
    Column("version", String(255), nullable=False),
    Column("server_json", Text, nullable=False),
    Column("published_at", String(40), nullable=False),
    UniqueConstraint("name", "version", name="uq_published_name_version"),
)

APPEND_ONLY = ("audit_events", "decisions", "published")


def append_only_triggers() -> list[str]:
    """SQLite triggers that refuse UPDATE and DELETE on the append-only tables."""
    return [
        f"CREATE TRIGGER IF NOT EXISTS {table}_no_{verb.lower()} BEFORE {verb} ON {table} "
        f"BEGIN SELECT RAISE(ABORT, '{table} is append-only'); END"
        for table in APPEND_ONLY
        for verb in ("UPDATE", "DELETE")
    ]
