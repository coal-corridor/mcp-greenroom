"""Importing the scanner adapter, and the scanner package with it, makes no connection."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = """
import socket
attempts = []
def record(self, address):
    attempts.append(address)
    raise OSError("blocked by the import probe")
socket.socket.connect = record
socket.socket.connect_ex = record
import mcp_greenroom.scanner.yara
import mcpscanner.core.analyzers.static_analyzer
print(len(attempts))
"""


def test_importing_the_adapter_makes_no_connection_attempt() -> None:
    env = {k: v for k, v in os.environ.items() if k != "LITELLM_LOCAL_MODEL_COST_MAP"}
    done = subprocess.run(  # noqa: S603 (fixed argv, no shell)
        [sys.executable, "-c", PROBE],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    assert done.stdout.strip().splitlines()[-1] == "0"
