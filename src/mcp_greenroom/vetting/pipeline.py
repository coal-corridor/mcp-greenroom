"""The decision order of docs/specs/mcp-greenroom.md, step by step. Implements Pipeline."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from mcp_greenroom.config import Settings
from mcp_greenroom.interfaces import ClassifierProvider, Scanner
from mcp_greenroom.models import Decision, Outcome, Reason, Submission


@dataclass(frozen=True)
class Policy:
    reject_threshold: float
    approve_threshold: float
    policy_version: str
    require_human_for_all: bool = False

    @classmethod
    def from_settings(cls, settings: Settings) -> "Policy":
        return cls(
            reject_threshold=settings.reject_threshold,
            approve_threshold=settings.approve_threshold,
            policy_version=settings.policy_version,
            require_human_for_all=settings.require_human_for_all,
        )


def _now() -> datetime:
    return datetime.now(UTC)


class VettingPipeline:
    """Implements interfaces.Pipeline."""

    def __init__(
        self,
        provider: ClassifierProvider,
        scanner: Scanner,
        policy: Policy,
        clock: Callable[[], datetime] = _now,
    ) -> None:
        self.provider = provider
        self.scanner = scanner
        self.policy = policy
        self.clock = clock

    def vet(self, submission: Submission) -> Decision:
        return Decision(
            outcome=Outcome.HUMAN_REVIEW,
            tier=None,
            reasons=(Reason(code="vetting.not_built", message="Not built yet."),),
            policy_version=self.policy.policy_version,
            decided_by="policy",
            decided_at=self.clock(),
        )
