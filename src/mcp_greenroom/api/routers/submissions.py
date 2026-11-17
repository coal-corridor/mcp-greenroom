"""Submit a server version for vetting."""

import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Response, status
from pydantic import BaseModel, ValidationError

from mcp_greenroom.api.dependencies import get_identity, get_pipeline, get_settings, get_store
from mcp_greenroom.api.errors import ApiError
from mcp_greenroom.config import Settings
from mcp_greenroom.fingerprint import fingerprint
from mcp_greenroom.interfaces import Pipeline, Refusal
from mcp_greenroom.logging import log_event
from mcp_greenroom.models import (
    AuditAction,
    AuditEvent,
    Decision,
    Identity,
    Reason,
    Submission,
)
from mcp_greenroom.store import SqlStore, StoredSubmission, VersionTaken

router = APIRouter(prefix="/submissions", tags=["submissions"])


class SubmissionResult(Decision):
    """The current decision with the submission it belongs to."""

    submission_id: str
    name: str | None
    version: str | None
    submitted_by: str


def log_decision(submission_id: str, decision: Decision) -> None:
    """One structured line per decision. Reason codes only: messages may quote tool text."""
    log_event(
        "decision",
        submission_id=submission_id,
        outcome=decision.outcome.value,
        tier=decision.tier.value if decision.tier else None,
        decided_by=decision.decided_by,
        policy_version=decision.policy_version,
        reason_codes=[reason.code for reason in decision.reasons],
    )


def _parse(payload: dict[str, Any]) -> Submission:
    try:
        submission = Submission.model_validate(payload)
    except ValidationError as exc:
        fields = sorted({".".join(str(p) for p in err["loc"]) for err in exc.errors()})
        raise Refusal(
            "validation.malformed",
            f"Submission is malformed at {', '.join(fields)}. "
            "Send a body with 'server' (a server.json object) and 'tools' (a list of tools).",
        ) from None
    if not submission.name or not submission.version:
        raise Refusal(
            "validation.malformed",
            "Submission is malformed: server.name and server.version must be non-empty strings. "
            "Set both in the server.json part and send it again.",
        )
    return submission


def _refuse(store: SqlStore, identity: Identity, settings: Settings, refusal: Refusal) -> ApiError:
    submission_id = str(uuid.uuid4())
    reason = Reason(code=refusal.rule_id, message=refusal.message)
    store.append_audit(
        AuditEvent(
            submission_id=submission_id,
            actor=identity.id,
            action=AuditAction.REFUSED,
            at=datetime.now(UTC),
            reasons=(reason,),
            policy_version=settings.policy_version,
        )
    )
    log_event("refusal", submission_id=submission_id, rule_id=refusal.rule_id)
    return ApiError(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        refusal.rule_id,
        refusal.message,
        received=refusal.received,
        submission_id=submission_id,
    )


def result_of(stored: StoredSubmission) -> SubmissionResult:
    return SubmissionResult(
        **stored.decision.model_dump(),
        submission_id=stored.id,
        name=stored.name,
        version=stored.version,
        submitted_by=stored.submitted_by,
    )


def _existing(store: SqlStore, submission: Submission, response: Response) -> BaseModel | None:
    """The stored decision for identical content; 409 for other content; None if new."""
    stored = store.find(str(submission.name), str(submission.version))
    if stored is None:
        return None
    if stored.fingerprint != fingerprint(submission):
        raise ApiError(
            status.HTTP_409_CONFLICT,
            "submission.version_exists",
            f"Submission refused: {submission.name} {submission.version} already has a decision "
            "and its content differs. Versions are immutable: publish the change as a new version.",
            submission_id=stored.id,
        )
    response.status_code = status.HTTP_200_OK
    return result_of(stored)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SubmissionResult)
def submit(
    response: Response,
    payload: Annotated[dict[str, Any], Body()],
    identity: Annotated[Identity, Depends(get_identity)],
    pipeline: Annotated[Pipeline, Depends(get_pipeline)],
    store: Annotated[SqlStore, Depends(get_store)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> BaseModel:
    try:
        submission = _parse(payload)
        if (existing := _existing(store, submission, response)) is not None:
            return existing
        decision = pipeline.vet(submission)
    except Refusal as refusal:
        raise _refuse(store, identity, settings, refusal) from None

    submission_id = str(uuid.uuid4())
    events = [
        AuditEvent(
            submission_id=submission_id,
            actor=identity.id,
            action=AuditAction.SUBMITTED,
            at=decision.decided_at,
            policy_version=decision.policy_version,
        ),
        AuditEvent(
            submission_id=submission_id,
            actor=decision.decided_by,
            action=AuditAction.POLICY_DECISION,
            at=decision.decided_at,
            reasons=decision.reasons,
            policy_version=decision.policy_version,
        ),
    ]
    try:
        store.create(
            submission_id, submission, fingerprint(submission), identity.id, decision, events
        )
    except VersionTaken:  # a concurrent submission of the same version won the race
        if (existing := _existing(store, submission, response)) is not None:
            return existing
        raise
    log_decision(submission_id, decision)
    return SubmissionResult(
        **decision.model_dump(),
        submission_id=submission_id,
        name=submission.name,
        version=submission.version,
        submitted_by=identity.id,
    )


def get_submission(store: SqlStore, submission_id: str) -> StoredSubmission:
    """The stored submission, or a 404 ApiError."""
    stored = store.get(submission_id)
    if stored is None:
        raise ApiError(
            status.HTTP_404_NOT_FOUND,
            "submission.not_found",
            "Lookup failed: no decided submission has this id. "
            "Use the submission_id returned when the version was submitted.",
        )
    return stored


@router.get("/{submission_id}", response_model=SubmissionResult)
def read_status(
    submission_id: str,
    identity: Annotated[Identity, Depends(get_identity)],
    store: Annotated[SqlStore, Depends(get_store)],
) -> BaseModel:
    return result_of(get_submission(store, submission_id))
