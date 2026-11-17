"""The scanner is built once and shared by request threads. Its thread safety is not verified,
so the adapter runs one scan at a time (integration review, "Not verified")."""

import asyncio
import threading
from pathlib import Path
from typing import Any

from mcp_greenroom.models import Tool
from mcp_greenroom.scanner.yara import YaraScanner


class _OverlapRecorder:
    """Stands in for the scanner's StaticAnalyzer and records how many scans overlap."""

    def __init__(self) -> None:
        self.active = 0
        self.peak = 0
        self._guard = threading.Lock()

    async def scan_tools_file(self, path: Path) -> list[dict[str, Any]]:
        with self._guard:
            self.active += 1
            self.peak = max(self.peak, self.active)
        await asyncio.sleep(0.05)
        with self._guard:
            self.active -= 1
        return []


def test_concurrent_scans_run_one_at_a_time() -> None:
    scanner = YaraScanner.__new__(YaraScanner)  # skip loading the real package
    recorder = _OverlapRecorder()
    scanner._static = recorder
    start = threading.Barrier(4)

    def scan_once() -> None:
        start.wait()
        assert scanner.scan([Tool(name="t", description="d")]) == []

    threads = [threading.Thread(target=scan_once) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert recorder.peak == 1
