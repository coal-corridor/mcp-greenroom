# Sample client configs

Synthetic. `amp-settings.json` follows the shape of Amp's `amp.mcpServers` setting: each
local server is a command and its arguments. The client simulator
(`src/mcp_greenroom/client_sim.py`) derives the package from the command (`npx` means npm,
`uvx` means pypi, `docker` means oci) and checks it against the registry list.

Expected against the main path: `payments` is allowed once `payments-readonly` 1.2.0 is
approved, `notes` is blocked (`poisoned-notes` is rejected, so never listed).
