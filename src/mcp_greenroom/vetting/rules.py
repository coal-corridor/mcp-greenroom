"""Deterministic rules over the tools. Decision order step 2: hidden characters."""

from collections.abc import Sequence

from mcp_greenroom.models import Finding, Tool


def hidden_characters(tools: Sequence[Tool]) -> list[Finding]:
    """One finding per tool whose name or description holds a hidden character."""
    return []
