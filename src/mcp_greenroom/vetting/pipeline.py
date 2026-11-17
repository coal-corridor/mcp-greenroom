"""The decision order of docs/specs/mcp-greenroom.md, step by step. Implements Pipeline.

First match wins. Read vet() against the numbered list in the spec.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from mcp_greenroom.config import Settings
from mcp_greenroom.interfaces import ClassifierProvider, Scanner
from mcp_greenroom.models import (
    Decision,
    Finding,
    Outcome,
    Reason,
    RiskResult,
    Submission,
    Tier,
    Tool,
)
from mcp_greenroom.vetting.rules import hidden_characters
from mcp_greenroom.vetting.validation import validate


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
        # Step 1. Malformed, not pinned, source not allowed, no tools: Refusal (422).
        validate(submission)
        return self._decide(submission.tools)

    def _decide(self, tools: Sequence[Tool]) -> Decision:
        # Step 2. Hidden characters in a name or description: rejected.
        hidden = hidden_characters(tools)
        if hidden:
            reasons = [
                Reason(
                    code=f.rule_id,
                    message="Hidden characters in the tool name or description.",
                    tool_name=f.tool_name,
                )
                for f in hidden
            ]
            return self._decision(Outcome.REJECTED, None, reasons, hidden)

        return self._decision(
            Outcome.HUMAN_REVIEW,
            None,
            [Reason(code="vetting.not_built", message="Not built yet.")],
            [],
        )

    def _decision(
        self,
        outcome: Outcome,
        tier: Tier | None,
        reasons: Sequence[Reason],
        findings: Sequence[Finding],
        risks: Sequence[RiskResult] = (),
    ) -> Decision:
        return Decision(
            outcome=outcome,
            tier=tier,
            reasons=tuple(reasons),
            findings=tuple(findings),
            risks=tuple(risks),
            policy_version=self.policy.policy_version,
            decided_by="policy",
            decided_at=self.clock(),
        )
