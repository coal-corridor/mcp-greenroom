"""Decision order step 1: refuse a malformed submission with 422 (interfaces.Refusal)."""

from mcp_greenroom.models import Submission


def validate(submission: Submission) -> None:
    """Raise Refusal when the submission breaks a step-1 rule. Return None when it passes."""
