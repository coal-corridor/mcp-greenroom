"""Shared data models. Frozen contract: a change here is a question to the user.

Tool names, descriptions, finding evidence and reviewer notes are untrusted text.
They are carried as data and never logged raw (see mcp_greenroom.logging).
"""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Outcome(StrEnum):
    APPROVED = "approved"
    HUMAN_REVIEW = "human_review"
    REJECTED = "rejected"


class Tier(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Capability(StrEnum):
    """Capability tags the classifier returns per tool. Tiers derive from them (vetting.md)."""

    CODE_EXEC = "code_exec"
    CREDENTIAL_ACCESS = "credential_access"
    LOCAL_READ = "local_read"
    LOCAL_WRITE = "local_write"
    NETWORK_EGRESS = "network_egress"


class FindingSource(StrEnum):
    RULE = "rule"  # our own rules, e.g. hidden characters
    SCANNER = "scanner"  # Cisco MCP Scanner YARA engine, evidence only
    CLASSIFIER = "classifier"


class Role(StrEnum):
    SUBMITTER = "submitter"
    REVIEWER = "reviewer"


class AuditAction(StrEnum):
    SUBMITTED = "submitted"
    REFUSED = "refused"  # validation refusal (422): no decision stored, audit event kept
    POLICY_DECISION = "policy_decision"
    APPROVED = "approved"  # human
    DECLINED = "declined"  # human


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)


class Tool(_Frozen):
    """One tool definition as the server declares it. Name and description are untrusted."""

    name: str
    description: str
    input_schema: dict[str, Any] = Field(default_factory=dict, alias="inputSchema")


class Submission(_Frozen):
    """One server version sent for vetting.

    `server` is a server.json document (contracts/server.schema.json). It is the only part
    ever published. `tools` sit beside it because server.json carries no tool definitions.
    Validation against the schema is vetting's first step (a 422 refusal), not this model's.
    """

    server: dict[str, Any]
    tools: list[Tool]

    @property
    def name(self) -> str | None:
        value = self.server.get("name")
        return value if isinstance(value, str) else None

    @property
    def version(self) -> str | None:
        value = self.server.get("version")
        return value if isinstance(value, str) else None


class Identity(_Frozen):
    """The caller, taken from the credential, never from the request body."""

    id: str
    roles: frozenset[Role]


class Reason(_Frozen):
    code: str  # stable reason or rule id, e.g. "classifier.no_recording"
    message: str
    tool_name: str | None = None


class Finding(_Frozen):
    """Evidence shown beside every outcome. `evidence` is untrusted text."""

    rule_id: str
    source: FindingSource
    severity: str
    threats: tuple[str, ...] = ()
    tool_name: str | None = None
    evidence: str = ""


class RiskResult(_Frozen):
    """The classifier's answer for one tool."""

    tool_name: str
    score: float = Field(ge=0.0, le=1.0)
    capabilities: frozenset[Capability] = frozenset()
    model_id: str
    prompt_hash: str


class Decision(_Frozen):
    outcome: Outcome
    tier: Tier | None
    reasons: tuple[Reason, ...]
    findings: tuple[Finding, ...] = ()
    risks: tuple[RiskResult, ...] = ()
    policy_version: str
    decided_by: str  # "policy" or a reviewer identity id
    decided_at: datetime


class AuditEvent(_Frozen):
    """Append-only. Never updated or deleted."""

    submission_id: str
    actor: str
    action: AuditAction
    at: datetime
    reasons: tuple[Reason, ...] = ()
    policy_version: str
