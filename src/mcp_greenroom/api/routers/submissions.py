"""Submit a server version for vetting."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from mcp_greenroom.api.dependencies import get_identity, get_pipeline, get_store
from mcp_greenroom.fingerprint import fingerprint
from mcp_greenroom.interfaces import Pipeline
from mcp_greenroom.models import AuditAction, AuditEvent, Decision, Identity, Submission
from mcp_greenroom.store import SqlStore

router = APIRouter(prefix="/submissions", tags=["submissions"])


class SubmissionResult(Decision):
    """The policy decision with the submission it belongs to."""

    submission_id: str
    name: str | None
    version: str | None
    submitted_by: str


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SubmissionResult)
def submit(
    submission: Submission,
    identity: Annotated[Identity, Depends(get_identity)],
    pipeline: Annotated[Pipeline, Depends(get_pipeline)],
    store: Annotated[SqlStore, Depends(get_store)],
) -> BaseModel:
    submission_id = str(uuid.uuid4())
    decision = pipeline.vet(submission)
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
