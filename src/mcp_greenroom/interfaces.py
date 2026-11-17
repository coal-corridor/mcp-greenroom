"""The seams between areas. Frozen contract: a change here is a question to the user.

Vetting implements Pipeline, ClassifierProvider and Scanner. Registry calls Pipeline
through the FastAPI dependency in mcp_greenroom.api.dependencies and owns the store.
Nothing from the store appears here: vetting never sees persistence.
"""

from collections.abc import Sequence
from typing import Protocol

from mcp_greenroom.models import Decision, Finding, RiskResult, Submission, Tool


class Refusal(Exception):  # noqa: N818 (approved contract name: a signal, not a bug)
    """Decision order step 1: the submission is refused with 422 and no decision is stored.

    rule_id is stable (e.g. "validation.version_not_pinned"). message is readable and
    leads with what failed. received names the offending value, escaped.
    """

    def __init__(self, rule_id: str, message: str, received: str = "") -> None:
        super().__init__(message)
        self.rule_id = rule_id
        self.message = message
        self.received = received


class ClassifierUnavailable(Exception):  # noqa: N818 (approved contract name)
    """The classifier could not answer (endpoint down, timeout, bad response). -> human review."""


class NoRecording(Exception):  # noqa: N818 (approved contract name)
    """Replay has no recording for this exact prompt version, name and description. -> human review.

    A miss is never guessed.
    """


class ScannerError(Exception):
    """The scanner failed to run or its output was unreadable. -> human review (fail closed)."""


class ClassifierProvider(Protocol):
    """Scores one tool. Replay by default; live only for the recording run."""

    def classify(self, tool: Tool) -> RiskResult:
        """Return the risk score and capability tags for one tool.

        Raises ClassifierUnavailable or NoRecording. Never returns a guessed result.
        """
        ...


class Scanner(Protocol):
    """Static scanner rules over the submitted tools. Evidence only: never grants, never rejects."""

    def scan(self, tools: Sequence[Tool]) -> list[Finding]:
        """Return one finding per rule match, empty when nothing matched. Raises ScannerError."""
        ...


class Pipeline(Protocol):
    """The vetting entry point the API calls."""

    def vet(self, submission: Submission) -> Decision:
        """Apply the decision order of docs/specs/mcp-greenroom.md and return the policy decision.

        Raises Refusal for step 1 (422). Any other failure inside vetting must already have
        been turned into a human-review Decision: this method fails closed.
        """
        ...


class Store(Protocol):
    """Persistence, owned by the registry area, which adds the methods in its pull request.

    Declared here only so the injection point has a type. Never imported by vetting/, risk/
    or scanner/.
    """
