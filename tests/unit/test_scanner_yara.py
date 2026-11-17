"""The YARA scanner adapter: findings as evidence, untrusted text escaped, failure is an error."""

import pytest

from mcp_greenroom.interfaces import ScannerError
from mcp_greenroom.models import FindingSource, Tool
from mcp_greenroom.scanner.yara import YaraScanner
from tests.unit.helpers import load_sample


def test_the_benign_sample_has_no_finding() -> None:
    assert YaraScanner().scan(load_sample("payments-readonly").tools) == []


def test_the_poisoned_sample_matches_on_its_hostile_tool_only() -> None:
    findings = YaraScanner().scan(load_sample("poisoned-notes").tools)
    assert findings
    assert {f.tool_name for f in findings} == {"search_notes"}
    for finding in findings:
        assert finding.source is FindingSource.SCANNER
        assert finding.rule_id.startswith("scanner.yara.")
        assert finding.severity == "HIGH"
        assert finding.threats
        assert finding.evidence.isascii()
        assert len(finding.evidence) <= 600


def test_a_scanner_that_cannot_run_raises_scanner_error(monkeypatch: pytest.MonkeyPatch) -> None:
    from mcpscanner.core.analyzers.static_analyzer import StaticAnalyzer

    async def broken(self: object, path: object) -> object:
        raise RuntimeError("rules failed to load")

    monkeypatch.setattr(StaticAnalyzer, "scan_tools_file", broken)
    with pytest.raises(ScannerError):
        YaraScanner().scan([Tool(name="t", description="d")])
