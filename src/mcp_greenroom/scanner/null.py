"""A scanner that finds nothing. Stands in on the seam until the YARA adapter lands.

Agreed with the user: the adapter is built after the evaluation gate, and is the first
thing cut if time runs out. With this scanner, step 6 of the decision order never fires.
"""

from collections.abc import Sequence

from mcp_greenroom.models import Finding, Tool


class NullScanner:
    """Implements interfaces.Scanner. Returns no findings."""

    def scan(self, tools: Sequence[Tool]) -> list[Finding]:
        return []
