"""The decision order of docs/specs/mcp-greenroom.md, step by step. Implements Pipeline.

First match wins. Read vet() against the numbered list in the spec.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from mcp_greenroom.config import Settings
from mcp_greenroom.interfaces import ClassifierProvider, NoRecording, Scanner
from mcp_greenroom.models import (
    Decision,
    Finding,
    FindingSource,
    Outcome,
    Reason,
    RiskResult,
    Submission,
    Tier,
    Tool,
)
from mcp_greenroom.risk.tiers import tier_for
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


MAX_EVIDENCE = 2000


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

        # Step 3. Classifier unavailable, or no recording for a tool: human review.
        risks, misses = self._classify(tools)
        if misses:
            return self._decision(Outcome.HUMAN_REVIEW, None, misses, [], risks)

        tier = tier_for(cap for r in risks for cap in r.capabilities)
        by_name = {tool.name: tool for tool in tools}

        # Step 4. Highest risk score at or above the reject threshold: rejected.
        over = [r for r in risks if r.score >= self.policy.reject_threshold]
        if over:
            reasons = [
                Reason(
                    code="classifier.reject_threshold",
                    message=(
                        f"Risk score {r.score:.2f} is at or above the reject threshold "
                        f"{self.policy.reject_threshold:.2f}."
                    ),
                    tool_name=r.tool_name,
                )
                for r in over
            ]
            evidence = [
                Finding(
                    rule_id="classifier.reject_threshold",
                    source=FindingSource.CLASSIFIER,
                    severity="high",
                    tool_name=r.tool_name,
                    evidence=by_name[r.tool_name].description[:MAX_EVIDENCE]
                    if r.tool_name in by_name
                    else "",
                )
                for r in over
            ]
            return self._decision(Outcome.REJECTED, tier, reasons, evidence, risks)

        # Step 5. Highest risk score at or above the approve threshold: human review.
        uncertain = [r for r in risks if r.score >= self.policy.approve_threshold]
        if uncertain:
            reasons = [
                Reason(
                    code="classifier.uncertain",
                    message=(
                        f"Risk score {r.score:.2f} is not below the approve threshold "
                        f"{self.policy.approve_threshold:.2f}."
                    ),
                    tool_name=r.tool_name,
                )
                for r in uncertain
            ]
            return self._decision(Outcome.HUMAN_REVIEW, tier, reasons, [], risks)

        return self._decision(
            Outcome.HUMAN_REVIEW,
            tier,
            [Reason(code="vetting.not_built", message="Not built yet.")],
            [],
            risks,
        )

    def _classify(self, tools: Sequence[Tool]) -> tuple[list[RiskResult], list[Reason]]:
        """Score every tool. A failure is a reason, never a guessed result."""
        risks: list[RiskResult] = []
        misses: list[Reason] = []
        for tool in tools:
            try:
                risks.append(self.provider.classify(tool))
            except NoRecording:
                misses.append(
                    Reason(
                        code="classifier.no_recording",
                        message="No recorded classifier response for this tool.",
                        tool_name=tool.name,
                    )
                )
            except Exception:  # ClassifierUnavailable, or anything else: fail closed
                misses.append(
                    Reason(
                        code="classifier.unavailable",
                        message="The classifier could not score this tool.",
                        tool_name=tool.name,
                    )
                )
        return risks, misses

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
