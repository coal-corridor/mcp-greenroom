"""Deterministic rules over the tools. Decision order step 2: hidden characters.

A hidden character is one a reader does not see: format characters (zero-width, bidi
controls, tag characters), control characters other than tab and line breaks, private
use, unassigned code points, the supplementary variation selectors, and letters that
render as blank (Hangul fillers, Braille blank, Khmer inherent vowels). The finding's
evidence names code points and positions, never the text itself.
"""

import unicodedata
from collections.abc import Sequence

from mcp_greenroom.models import Finding, FindingSource, Tool

RULE_ID = "rule.hidden_characters"
MAX_LISTED = 5

_HIDDEN_CATEGORIES = frozenset({"Cf", "Cc", "Co", "Cn"})
_VISIBLE_CONTROLS = frozenset("\t\n\r")
_SUPPLEMENTARY_SELECTORS = range(0xE0100, 0xE01F0)
# Letters and symbols that render as blank: Hangul fillers, Braille blank, Khmer inherent
# vowels. Their categories (Lo, So, Mn) look harmless, so they are listed by code point.
_INVISIBLE_LETTERS = frozenset("\u115f\u1160\u17b4\u17b5\u2800\u3164\uffa0")


def is_hidden(char: str) -> bool:
    if char in _VISIBLE_CONTROLS:
        return False
    return (
        unicodedata.category(char) in _HIDDEN_CATEGORIES
        or ord(char) in _SUPPLEMENTARY_SELECTORS
        or char in _INVISIBLE_LETTERS
    )


def _positions(field: str, text: str) -> list[str]:
    return [f"U+{ord(c):04X} at {field}[{i}]" for i, c in enumerate(text) if is_hidden(c)]


def hidden_characters(tools: Sequence[Tool]) -> list[Finding]:
    """One finding per tool whose name or description holds a hidden character."""
    findings = []
    for tool in tools:
        hits = _positions("name", tool.name) + _positions("description", tool.description)
        if not hits:
            continue
        listed = ", ".join(hits[:MAX_LISTED])
        more = f" and {len(hits) - MAX_LISTED} more" if len(hits) > MAX_LISTED else ""
        findings.append(
            Finding(
                rule_id=RULE_ID,
                source=FindingSource.RULE,
                severity="high",
                tool_name=tool.name,
                evidence=f"Hidden characters: {listed}{more}.",
            )
        )
    return findings
