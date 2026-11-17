"""Submit a server version for vetting."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from mcp_greenroom.api.dependencies import get_identity, get_pipeline
from mcp_greenroom.interfaces import Pipeline
from mcp_greenroom.models import Decision, Identity, Submission

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
) -> BaseModel:
    decision = pipeline.vet(submission)
    return SubmissionResult(
        **decision.model_dump(),
        submission_id=str(uuid.uuid4()),
        name=submission.name,
        version=submission.version,
        submitted_by=identity.id,
    )
