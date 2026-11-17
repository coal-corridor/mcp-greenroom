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
MAX_PAGES = 1000

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


class RegistryUnusableError(Exception):
    """The registry list could not be read: unreachable, a server error, or not a ServerList."""


def _packages(record: object) -> set[tuple[str, str]]:
    server = record.get("server") if isinstance(record, dict) else None
    packages = server.get("packages", []) if isinstance(server, dict) else None
    if not isinstance(packages, list):
        raise RegistryUnusableError("a record has no server object or no packages list")
    found = set()
    for package in packages:
        kind = package.get("registryType") if isinstance(package, dict) else None
        ident = package.get("identifier") if isinstance(package, dict) else None
        if not (isinstance(kind, str) and isinstance(ident, str)):
            raise RegistryUnusableError("a package has no registryType or identifier string")
        found.add((kind, ident))
    return found


def _page(registry: httpx.Client, cursor: str | None) -> dict[str, Any]:
    params = {"cursor": cursor} if cursor else {}
    try:
        response = registry.get(LIST_PATH, params=params)
        response.raise_for_status()
        body = response.json()
    except httpx.HTTPStatusError as exc:
        raise RegistryUnusableError(f"HTTP {exc.response.status_code}") from None
    except httpx.HTTPError as exc:
        raise RegistryUnusableError(f"unreachable ({type(exc).__name__})") from None
    except ValueError:
        raise RegistryUnusableError("the reply is not JSON") from None
    if not isinstance(body, dict) or not isinstance(body.get("servers"), list):
        raise RegistryUnusableError("the reply has no servers list")
    return body


def _listed(registry: httpx.Client) -> set[tuple[str, str]]:
    listed: set[tuple[str, str]] = set()
    cursor: str | None = None
    seen: set[str] = set()
    for _ in range(MAX_PAGES):
        body = _page(registry, cursor)
        listed |= {package for record in body["servers"] for package in _packages(record)}
        metadata = body.get("metadata")
        cursor = metadata.get("nextCursor") if isinstance(metadata, dict) else None
        if not cursor:
            return listed
        if not isinstance(cursor, str) or cursor in seen:
            raise RegistryUnusableError("the paging cursor repeats or is not a string")
        seen.add(cursor)
    raise RegistryUnusableError(f"the list runs past {MAX_PAGES} pages")


def check_config(config_path: Path, registry: httpx.Client) -> list[Verdict]:
    servers: dict[str, dict[str, Any]] = json.loads(config_path.read_text(encoding="utf-8"))[
        SERVERS_KEY
    ]
    try:
        listed = _listed(registry)
    except RegistryUnusableError as exc:
        reason = f"registry list unusable: {exc}, so every server is blocked"
        return [Verdict(name, False, reason) for name in servers]
    verdicts = []
    for name, entry in servers.items():
        package = _package(entry)
        if package in listed:
            verdicts.append(Verdict(name, True, f"{package[0]} package {package[1]} is listed"))
        else:
            verdicts.append(Verdict(name, False, "package is not on the registry list"))
    return verdicts
