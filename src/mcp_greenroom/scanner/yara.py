"""Scanner rules: the Cisco MCP Scanner's YARA engine in static mode, offline, no key.

Importing mcp_greenroom.config first sets LITELLM_LOCAL_MODEL_COST_MAP, so the scanner's
import of litellm does not fetch a remote cost map.
"""

import mcp_greenroom.config  # noqa: F401  (must load before mcpscanner)
