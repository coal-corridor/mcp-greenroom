"""Decision order step 2: hidden characters in a tool name or description."""

import pytest

from mcp_greenroom.models import FindingSource, Tool
from mcp_greenroom.vetting.rules import hidden_characters
from tests.unit.helpers import load_sample

HIDDEN = {
    "zero width space": "​",
    "zero width joiner": "‍",
    "right-to-left override": "‮",
    "byte order mark": "﻿",
    "soft hyphen": "­",
    "tag character": "\U000e0041",
    "supplementary variation selector": "\U000e0100",
    "private use": "",
    "unassigned": "͸",
    "escape": "\x1b",
    "null": "\x00",
}


@pytest.mark.parametrize("char", HIDDEN.values(), ids=HIDDEN.keys())
def test_a_hidden_character_in_a_description_is_a_finding(char: str) -> None:
    tool = Tool(name="get_balance", description=f"Returns the balance.{char} Read only.")
    findings = hidden_characters([tool])
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "rule.hidden_characters"
    assert finding.source is FindingSource.RULE
    assert finding.tool_name == "get_balance"
    assert f"U+{ord(char):04X}" in finding.evidence
    assert "description[20]" in finding.evidence


def test_a_hidden_character_in_a_name_is_a_finding() -> None:
    findings = hidden_characters([Tool(name="get​balance", description="Balance.")])
    assert [f.rule_id for f in findings] == ["rule.hidden_characters"]
    assert "name[3]" in findings[0].evidence


def test_the_evidence_never_carries_the_hidden_character_itself() -> None:
    tool = Tool(name="t", description="a‮b\U000e0041c")
    evidence = hidden_characters([tool])[0].evidence
    assert evidence.isascii()


@pytest.mark.parametrize(
    "description",
    [
        "Plain text.\nSecond line.\tTabbed.\r\n",
        "Café, naïve, Zürich, 東京, ₹, €.",
        "Warning ⚠️ sign with its usual emoji selector.",
    ],
)
def test_ordinary_text_has_no_finding(description: str) -> None:
    assert hidden_characters([Tool(name="ok", description=description)]) == []


@pytest.mark.parametrize(
    "slug", ["payments-readonly", "poisoned-notes", "unrecorded-reporter", "ambiguous-exporter"]
)
def test_the_samples_have_no_hidden_characters(slug: str) -> None:
    assert hidden_characters(load_sample(slug).tools) == []


def test_only_the_tool_with_the_hidden_character_is_named() -> None:
    tools = [Tool(name="clean", description="Fine."), Tool(name="dirty", description="x​y")]
    assert [f.tool_name for f in hidden_characters(tools)] == ["dirty"]


INVISIBLE_LETTERS = ["ㅤ", "ﾠ", "ᅟ", "ᅠ", "⠀", "឴", "឵"]


@pytest.mark.parametrize(
    "char", INVISIBLE_LETTERS, ids=[f"U+{ord(c):04X}" for c in INVISIBLE_LETTERS]
)
def test_an_invisible_letter_is_a_hidden_character(char: str) -> None:
    findings = hidden_characters([Tool(name="t", description=f"Visible{char}text.")])
    assert [f.rule_id for f in findings] == ["rule.hidden_characters"]
    assert f"U+{ord(char):04X}" in findings[0].evidence
