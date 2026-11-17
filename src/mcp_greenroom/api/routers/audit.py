"""Read the audit trail of one submission, refusals included. There is no write route."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from mcp_greenroom.api.dependencies import get_identity, get_store
from mcp_greenroom.api.errors import ApiError
from mcp_greenroom.models import AuditEvent, Identity
from mcp_greenroom.store import SqlStore

router = APIRouter(prefix="/submissions", tags=["audit"])


class AuditTrail(BaseModel):
    submission_id: str
    events: list[AuditEvent]


@router.get("/{submission_id}/audit", response_model=AuditTrail)
def read_audit(
    submission_id: str,
    identity: Annotated[Identity, Depends(get_identity)],
    store: Annotated[SqlStore, Depends(get_store)],
) -> AuditTrail:
    events = store.audit(submission_id)
    if not events:
        raise ApiError(
            status.HTTP_404_NOT_FOUND,
            "submission.not_found",
            "Lookup failed: no submission or refusal has this id. "
            "Use the submission_id returned by the submit call.",
        )
    return AuditTrail(submission_id=submission_id, events=events)
