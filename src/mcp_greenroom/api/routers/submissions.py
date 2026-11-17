"""Submit a server version for vetting."""

import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, status
from pydantic import BaseModel, ValidationError

from mcp_greenroom.api.dependencies import get_identity, get_pipeline, get_settings, get_store
from mcp_greenroom.api.errors import ApiError
from mcp_greenroom.config import Settings
from mcp_greenroom.fingerprint import fingerprint
from mcp_greenroom.interfaces import Pipeline, Refusal
from mcp_greenroom.models import (
    AuditAction,
    AuditEvent,
    Decision,
    Identity,
    Reason,
    Submission,
)
from mcp_greenroom.store import SqlStore

router = APIRouter(prefix="/submissions", tags=["submissions"])


class SubmissionResult(Decision):
    """The current decision with the submission it belongs to."""

    submission_id: str
    name: str | None
    version: str | None
    submitted_by: str


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
    return ApiError(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        refusal.rule_id,
        refusal.message,
        received=refusal.received,
        submission_id=submission_id,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SubmissionResult)
def submit(
    payload: Annotated[dict[str, Any], Body()],
    identity: Annotated[Identity, Depends(get_identity)],
    pipeline: Annotated[Pipeline, Depends(get_pipeline)],
    store: Annotated[SqlStore, Depends(get_store)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> BaseModel:
    try:
        submission = _parse(payload)
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
    store.create(submission_id, submission, fingerprint(submission), identity.id, decision, events)
    return SubmissionResult(
        **decision.model_dump(),
        submission_id=submission_id,
        name=submission.name,
        version=submission.version,
        submitted_by=identity.id,
    )
