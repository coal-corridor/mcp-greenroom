"""Decision order step 1: refuse a malformed submission with 422 (interfaces.Refusal).

Every refusal carries a stable rule id and a message in three parts: what failed, what
was received (escaped, truncated), what to do. The received value is untrusted text.
"""

import json
import re
from functools import cache
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema.exceptions import best_match

from mcp_greenroom.interfaces import Refusal
from mcp_greenroom.models import Submission, Tool
from mcp_greenroom.vetting.policy import (
    ALLOWED_SOURCES,
    REGISTRY_OVERRIDE_FLAGS,
    REGISTRY_OVERRIDE_VARIABLES,
)

MAX_RECEIVED = 80
SCHEMA_PATH = Path(__file__).resolve().parents[3] / "contracts" / "server.schema.json"

# One exact version: digits first (an optional "v"), dot-separated numbers, then an optional
# pre-release or build suffix. Refuses tags ("latest", "next"), ranges and wildcards.
_PINNED = re.compile(r"v?\d+(?:\.\d+)*(?:[-+][0-9A-Za-z.+-]+)?")


def escaped(value: object) -> str:
    """Untrusted value as a short, ASCII-only, quoted string."""
    text = value if isinstance(value, str) else repr(value)
    if len(text) > MAX_RECEIVED:
        text = text[:MAX_RECEIVED] + "..."
    return ascii(text)


def _refuse(rule_id: str, failed: str, value: object, todo: str) -> Refusal:
    received = escaped(value)
    return Refusal(rule_id, f"{failed}. Received {received}. {todo}", received)


def is_pinned(version: str) -> bool:
    return _PINNED.fullmatch(version) is not None


def _check_versions(server: dict[str, Any]) -> None:
    versions = [("version", server.get("version"))]
    packages = server.get("packages")
    if isinstance(packages, list):
        versions += [
            (f"packages[{i}].version", package.get("version"))
            for i, package in enumerate(packages)
            if isinstance(package, dict)
        ]
    for where, version in versions:
        if isinstance(version, str) and not is_pinned(version):
            raise _refuse(
                "validation.version_not_pinned",
                f"Version is not pinned: {where} must be one exact version",
                version,
                "Submit an exact version such as 1.2.0: no tag, range or wildcard.",
            )


@cache
def _schema_validator() -> jsonschema.Draft7Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return jsonschema.Draft7Validator(schema)


def _check_schema(server: dict[str, Any]) -> None:
    error = best_match(_schema_validator().iter_errors(server))
    if error is None:
        return
    where = "/" + "/".join(str(part) for part in error.absolute_path)
    raise _refuse(
        "validation.schema",
        f"Server manifest does not fit the schema at {where}: the '{error.validator}' rule failed",
        error.instance,
        "Fix server.json against contracts/server.schema.json (2025-12-11) and submit again.",
    )


# Package-name grammar per registry: a bare name, never a specifier that can point
# elsewhere (git, file, tarball URL, version or extras).
_NAME_GRAMMAR = {
    "npm": re.compile(r"(?:@[a-z0-9~-][a-z0-9._~-]*/)?[a-z0-9~-][a-z0-9._~-]{0,213}"),
    "pypi": re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,198}[A-Za-z0-9])?"),
}


def _overrides_registry(package: dict[str, Any]) -> bool:
    for field in ("runtimeArguments", "packageArguments"):
        for argument in package.get(field) or []:
            if not isinstance(argument, dict):
                continue
            for key in ("name", "value"):
                text = argument.get(key)
                if isinstance(text, str) and text.split("=", 1)[0] in REGISTRY_OVERRIDE_FLAGS:
                    return True
    for variable in package.get("environmentVariables") or []:
        name = variable.get("name") if isinstance(variable, dict) else None
        if isinstance(name, str) and name.upper() in REGISTRY_OVERRIDE_VARIABLES:
            return True
    return False


def _source_allowed(package: dict[str, Any]) -> bool:
    allowed = ALLOWED_SOURCES.get(package.get("registryType", ""))
    base = package.get("registryBaseUrl", allowed)
    identifier = package.get("identifier", "")
    return (
        allowed is not None
        and isinstance(base, str)
        and base.rstrip("/") == allowed
        and isinstance(identifier, str)
        and _NAME_GRAMMAR[package["registryType"]].fullmatch(identifier) is not None
        and not _overrides_registry(package)
    )


def _check_sources(server: dict[str, Any]) -> None:
    remotes = server.get("remotes") or []
    if remotes:  # this slice vets packages only; a remote endpoint is not an allowed source
        raise _refuse(
            "validation.source_not_allowed",
            "Package source is not allowed: the server lists remotes, which this registry "
            "does not vet",
            [r.get("url") for r in remotes if isinstance(r, dict)],
            "Remove 'remotes' and submit the server as a package from an allowed registry.",
        )
    packages = server.get("packages") or []
    todo = (
        f"Publish the package to an allowed registry ({', '.join(ALLOWED_SOURCES.values())}) "
        "and submit it by name."
    )
    if not packages:
        raise _refuse(
            "validation.source_not_allowed",
            "Package source is not allowed: the server lists no package",
            packages,
            todo,
        )
    for package in packages:
        if not _source_allowed(package):
            source = (
                f"{package.get('registryType')} {package.get('registryBaseUrl', '(default)')} "
                f"{package.get('identifier')}"
            )
            raise _refuse(
                "validation.source_not_allowed",
                "Package source is not allowed",
                source,
                todo,
            )


def _check_tools(tools: list[Tool]) -> None:
    if not tools:
        raise _refuse(
            "validation.no_tools",
            "No tools: the submission lists no tool definitions",
            tools,
            "Send the server's tools/list output in 'tools' and submit again.",
        )


def validate(submission: Submission) -> None:
    """Raise Refusal when the submission breaks a step-1 rule. Return None when it passes."""
    _check_versions(submission.server)
    _check_schema(submission.server)
    _check_sources(submission.server)
    _check_tools(submission.tools)
