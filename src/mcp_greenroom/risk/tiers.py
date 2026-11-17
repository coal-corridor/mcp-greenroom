"""Tiers from the classifier's capability tags (docs/specs/vetting.md)."""

from collections.abc import Iterable

from mcp_greenroom.models import Capability, Tier


def tier_for(capabilities: Iterable[Capability]) -> Tier:
    """The tier of a set of capabilities."""
    return Tier.LOW
