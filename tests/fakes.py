"""Fakes for the seams in mcp_greenroom.interfaces, so registry and edge can build before vetting.

The fake pipeline reaches the outcome in sample-data/servers/README.md for each named
sample. Its reason codes are placeholders: assert the outcome and tier, not the code.
Swap it in with app.dependency_overrides[get_pipeline] = lambda: FakePipeline().
"""

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime

from mcp_greenroom.interfaces import ClassifierUnavailable, NoRecording, Refusal
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

POLICY_VERSION = "fake-policy"


def _decision(outcome: Outcome, tier: Tier | None, *reasons: Reason, **extra: object) -> Decision:
    return Decision(
        outcome=outcome,
        tier=tier,
        reasons=reasons,
        policy_version=POLICY_VERSION,
        decided_by="policy",
        decided_at=datetime.now(UTC),
        **extra,  # type: ignore[arg-type]
    )


class FakePipeline:
    """Implements interfaces.Pipeline by sample name. Unknown names go to human review."""

    def __init__(self) -> None:
        self.calls: list[Submission] = []

    def vet(self, submission: Submission) -> Decision:
        self.calls.append(submission)
        slug = (submission.name or "").removeprefix("com.examplebank/")
        if submission.version in (None, "", "latest"):
            raise Refusal("fake.version_not_pinned", "Version is not pinned.", "latest")
        if slug == "payments-readonly":
            return _decision(Outcome.APPROVED, Tier.LOW, Reason(code="fake.low", message="Low."))
        if slug == "poisoned-notes":
            tool = submission.tools[0]
            finding = Finding(
                rule_id="fake.reject_threshold",
                source=FindingSource.CLASSIFIER,
                severity="high",
                tool_name=tool.name,
                evidence=tool.description,
            )
            reason = Reason(code="fake.reject_threshold", message="Score.", tool_name=tool.name)
            return _decision(Outcome.REJECTED, Tier.HIGH, reason, findings=(finding,))
        if slug == "ambiguous-exporter":
            reason = Reason(code="fake.tier_medium", message="Medium.")
            return _decision(Outcome.HUMAN_REVIEW, Tier.MEDIUM, reason)
        if slug == "unrecorded-reporter":
            reason = Reason(code="fake.no_recording", message="No recording.")
            return _decision(Outcome.HUMAN_REVIEW, None, reason)
        return _decision(Outcome.HUMAN_REVIEW, None, Reason(code="fake.unknown", message="?"))


class FakeProvider:
    """Implements interfaces.ClassifierProvider from a fixed table of results by tool name."""

    def __init__(
        self, results: Mapping[str, RiskResult] | None = None, *, unavailable: bool = False
    ) -> None:
        self.results = dict(results or {})
        self.unavailable = unavailable

    def classify(self, tool: Tool) -> RiskResult:
        if self.unavailable:
            raise ClassifierUnavailable("fake provider set to unavailable")
        if tool.name not in self.results:
            raise NoRecording("fake provider has no result for this tool")
        return self.results[tool.name]


class FakeScanner:
    """Implements interfaces.Scanner. Returns the given findings, whatever the tools."""

    def __init__(self, findings: Sequence[Finding] = ()) -> None:
        self.findings = list(findings)

    def scan(self, tools: Sequence[Tool]) -> list[Finding]:
        return list(self.findings)
