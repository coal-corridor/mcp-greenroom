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
        scanned, scanner_failed = self._scan(tools)

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

        # Step 6. A scanner rule matched on any tool: human review. A failed scan counts.
        if scanned or scanner_failed:
            reasons = [
                Reason(
                    code="scanner.match",
                    message="A scanner rule matched this tool.",
                    tool_name=name,
                )
                for name in dict.fromkeys(f.tool_name for f in scanned)
            ]
            if scanner_failed:
                reasons.append(
                    Reason(code="scanner.unavailable", message="The scanner could not run.")
                )
            return self._decision(Outcome.HUMAN_REVIEW, tier, reasons, scanned, risks)

        # Step 7. Tier medium or high: human review.
        if tier is not Tier.LOW:
            capabilities = sorted({cap.value for r in risks for cap in r.capabilities})
            reason = Reason(
                code=f"tier.{tier.value}",
                message=f"Tier {tier.value}, from capabilities: {', '.join(capabilities)}.",
            )
            return self._decision(Outcome.HUMAN_REVIEW, tier, [reason], [], risks)

        # Step 8. Tier low: approved by policy, or human review when policy demands a human.
        if self.policy.require_human_for_all:
            reason = Reason(
                code="policy.human_required",
                message="Tier low, but policy demands a human for every server.",
            )
            return self._decision(Outcome.HUMAN_REVIEW, tier, [reason], [], risks)
        reason = Reason(
            code="policy.tier_low",
            message=(
                f"Tier low, every risk score below {self.policy.approve_threshold:.2f}, "
                "no rule or scanner match."
            ),
        )
        return self._decision(Outcome.APPROVED, tier, [reason], [], risks)

    def _scan(self, tools: Sequence[Tool]) -> tuple[list[Finding], bool]:
        """Scanner findings, and whether the scan failed. Evidence only."""
        try:
            return list(self.scanner.scan(tools)), False
        except Exception:  # ScannerError, or anything else: fail closed
            return [], True

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
