"""Tiers from the classifier's capability tags (docs/specs/vetting.md).

High: code execution or credential access, or local read together with network egress.
Medium: local write or network egress. Low: everything else.
"""

from collections.abc import Iterable

from mcp_greenroom.models import Capability, Tier

_HIGH_ALONE = frozenset({Capability.CODE_EXEC, Capability.CREDENTIAL_ACCESS})
_HIGH_TOGETHER = frozenset({Capability.LOCAL_READ, Capability.NETWORK_EGRESS})
_MEDIUM = frozenset({Capability.LOCAL_WRITE, Capability.NETWORK_EGRESS})


def tier_for(capabilities: Iterable[Capability]) -> Tier:
    """The tier of a set of capabilities."""
    found = frozenset(capabilities)
    if found & _HIGH_ALONE or _HIGH_TOGETHER <= found:
        return Tier.HIGH
    if found & _MEDIUM:
        return Tier.MEDIUM
    return Tier.LOW
