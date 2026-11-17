"""Scanner rules: the Cisco MCP Scanner's YARA engine in static mode, offline, no key.

Importing mcp_greenroom.config first sets LITELLM_LOCAL_MODEL_COST_MAP, so the scanner's
import of litellm does not fetch a remote cost map. The scanner's output is untrusted
text: severity and threat names are kept as the scanner gives them, escaped; the summary
is escaped and truncated. Any failure, or a scan that did not complete, is ScannerError.
"""

import asyncio
import json
import re
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import mcp_greenroom.config  # noqa: F401  (must load before mcpscanner)
from mcp_greenroom.interfaces import ScannerError
from mcp_greenroom.models import Finding, FindingSource, Tool

MAX_EVIDENCE = 500
MAX_LABEL = 60


def _label(value: object) -> str:
    text = str(value)[:MAX_LABEL]
    return ascii(text)[1:-1]


def _slug(threat: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", threat.lower()).strip("_") or "unknown"


class YaraScanner:
    """Implements interfaces.Scanner."""

    def __init__(self) -> None:
        # Imported here: the package is heavy (about 2.5 s), and only this adapter needs it.
        from mcpscanner.core.analyzers.static_analyzer import (  # type: ignore[import-untyped]
            StaticAnalyzer,
        )
        from mcpscanner.core.analyzers.yara_analyzer import (  # type: ignore[import-untyped]
            YaraAnalyzer,
        )

        self._static = StaticAnalyzer(analyzers=[YaraAnalyzer()])

    def _run(self, tools: Sequence[Tool]) -> list[dict[str, Any]]:
        payload = {"tools": [t.model_dump(by_alias=True) for t in tools]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tools.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            results: list[dict[str, Any]] = asyncio.run(self._static.scan_tools_file(path))
        return results

    def scan(self, tools: Sequence[Tool]) -> list[Finding]:
        try:
            results = self._run(tools)
            findings: list[Finding] = []
            for result in results:
                if result.get("status") != "completed" or result.get("analyzer_errors"):
                    raise ScannerError(
                        "Scanner did not complete: status "
                        f"{_label(result.get('status'))}. The submission goes to human review."
                    )
                for raw in result.get("findings", []):
                    threat = _label(raw.threat_category)
                    findings.append(
                        Finding(
                            rule_id=f"scanner.yara.{_slug(threat)}",
                            source=FindingSource.SCANNER,
                            severity=_label(raw.severity),
                            threats=(threat,),
                            tool_name=str(result.get("tool_name")),
                            evidence=ascii(str(raw.summary)[:MAX_EVIDENCE])[1:-1],
                        )
                    )
            return findings
        except ScannerError:
            raise
        except Exception as exc:
            raise ScannerError(
                f"Scanner failed: {type(exc).__name__}. The submission goes to human review."
            ) from None
