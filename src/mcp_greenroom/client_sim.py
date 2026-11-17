"""Client simulator: a simulation of Amp's documented registry check, not Amp itself.

It reads a client config in the shape of Amp's `amp.mcpServers` setting, derives each local
server's package from its launch command, and allows the server only when the registry list
(`GET /v0.1/servers`, pinned in contracts/registry-openapi.yaml) carries a package with the
same registry type and identifier.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

SERVERS_KEY = "amp.mcpServers"
LIST_PATH = "/v0.1/servers"

# Launch command -> registry type.
_RUNNERS = {"npx": "npm", "uvx": "pypi", "docker": "oci"}


@dataclass(frozen=True)
class Verdict:
    server: str
    allowed: bool
    reason: str


def _strip_version(spec: str) -> str:
    """'@scope/pkg@1.2.0' -> '@scope/pkg'. The version is not part of the match."""
    at = spec.rfind("@")
    return spec[:at] if at > 0 else spec


def _package(entry: dict[str, Any]) -> tuple[str, str] | None:
    registry_type = _RUNNERS.get(str(entry.get("command", "")))
    args = [a for a in entry.get("args", []) if isinstance(a, str) and not a.startswith("-")]
    if registry_type is None or not args:
        return None
    return registry_type, _strip_version(args[0])


def _listed(registry: httpx.Client) -> set[tuple[str, str]]:
    body = registry.get(LIST_PATH).json()
    return {
        (package["registryType"], package["identifier"])
        for record in body["servers"]
        for package in record["server"].get("packages", [])
    }


def check_config(config_path: Path, registry: httpx.Client) -> list[Verdict]:
    servers: dict[str, dict[str, Any]] = json.loads(config_path.read_text(encoding="utf-8"))[
        SERVERS_KEY
    ]
    listed = _listed(registry)
    verdicts = []
    for name, entry in servers.items():
        package = _package(entry)
        if package in listed:
            verdicts.append(Verdict(name, True, f"{package[0]} package {package[1]} is listed"))
        else:
            verdicts.append(Verdict(name, False, "package is not on the registry list"))
    return verdicts
