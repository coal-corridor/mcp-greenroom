"""Fingerprint of one submission: the manifest and the tool definitions."""

from mcp_greenroom.models import Submission


def fingerprint(submission: Submission) -> str:
    """Return "sha256:<hex>" over canonical JSON of the server.json and the tools.

    Stable under key order and tool order. Any change to the manifest or to a tool
    name, description or input schema changes it.
    """
    raise NotImplementedError
