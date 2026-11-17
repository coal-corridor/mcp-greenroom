"""A reviewer approves or declines a case in human review. Never their own submission."""

from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict

from mcp_greenroom.api.dependencies import get_identity, get_store
from mcp_greenroom.api.errors import ApiError
from mcp_greenroom.api.routers.submissions import (
    SubmissionResult,
    get_submission,
    log_decision,
    result_of,
)
from mcp_greenroom.models import AuditAction, AuditEvent, Decision, Identity, Outcome, Reason, Role
from mcp_greenroom.store import NotPending, SqlStore

router = APIRouter(prefix="/submissions", tags=["reviews"])

_ACTIONS = {
    "approve": (Outcome.APPROVED, AuditAction.APPROVED, "review.approved"),
    "decline": (Outcome.REJECTED, AuditAction.DECLINED, "review.declined"),
}


class ReviewRequest(BaseModel):
    """The reviewer is the caller's credential: the body names no identity."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["approve", "decline"]
    note: str


@router.post("/{submission_id}/review", response_model=SubmissionResult)
def review(
    submission_id: str,
    request: ReviewRequest,
    identity: Annotated[Identity, Depends(get_identity)],
    store: Annotated[SqlStore, Depends(get_store)],
) -> BaseModel:
    stored = get_submission(store, submission_id)
    if Role.REVIEWER not in identity.roles:
        raise ApiError(
            status.HTTP_403_FORBIDDEN,
            "review.not_reviewer",
            "Review refused: the caller does not hold the reviewer role. "
            "Ask a reviewer to decide this case.",
        )
    if identity.id == stored.submitted_by:  # identities, not roles
        raise ApiError(
            status.HTTP_403_FORBIDDEN,
            "review.reviewer_is_submitter",
            "Review refused: the reviewer submitted this version. Another reviewer must decide it.",
        )
    note = request.note.strip()
    if not note:
        raise ApiError(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "review.note_required",
            "Review refused: the note is empty. Say why in the note and send it again.",
        )

    outcome, action, code = _ACTIONS[request.action]
    policy = stored.decision
    now = datetime.now(UTC)
    reasons = (Reason(code=code, message=note),)
    decision = Decision(
        outcome=outcome,
        tier=policy.tier,
        reasons=reasons,
        findings=policy.findings,
        risks=policy.risks,
        policy_version=policy.policy_version,
        decided_by=identity.id,
        decided_at=now,
    )
    event = AuditEvent(
        submission_id=stored.id,
        actor=identity.id,
        action=action,
        at=now,
        reasons=reasons,
        policy_version=policy.policy_version,
    )
    try:
        store.decide(stored.id, decision, event)
    except NotPending:
        raise ApiError(
            status.HTTP_409_CONFLICT,
            "review.not_pending",
            f"Review refused: this submission is {policy.outcome.value}, not in human review. "
            "A decided version is final: submit a new version instead.",
        ) from None
    log_decision(stored.id, decision)
    return result_of(get_submission(store, stored.id))
