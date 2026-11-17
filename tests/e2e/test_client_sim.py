"""Client check (edge.md): the simulator allows listed servers and blocks the rest."""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from mcp_greenroom.client_sim import check_config

ROOT = Path(__file__).resolve().parents[2]
AMP_CONFIG = ROOT / "sample-data" / "client-configs" / "amp-settings.json"


def _record(name: str, registry_type: str, identifier: str) -> dict[str, Any]:
    return {
        "server": {
            "name": name,
            "description": "Synthetic.",
            "version": "1.2.0",
            "packages": [
                {
                    "registryType": registry_type,
                    "identifier": identifier,
                    "version": "1.2.0",
                    "transport": {"type": "stdio"},
                }
            ],
        }
    }


def _registry(*records: dict[str, Any]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v0.1/servers"
        return httpx.Response(200, json={"servers": list(records), "metadata": {"count": 1}})

    return httpx.Client(base_url="http://registry.test", transport=httpx.MockTransport(handler))


def test_listed_server_is_allowed() -> None:
    payments = _record(
        "com.examplebank/payments-readonly", "npm", "@examplebank/payments-readonly-mcp"
    )

    allowed = {v.server for v in check_config(AMP_CONFIG, _registry(payments)) if v.allowed}

    assert "payments" in allowed


def test_unlisted_server_is_blocked() -> None:
    payments = _record(
        "com.examplebank/payments-readonly", "npm", "@examplebank/payments-readonly-mcp"
    )

    verdicts = {v.server: v for v in check_config(AMP_CONFIG, _registry(payments))}

    assert verdicts["notes"].allowed is False
    assert verdicts["payments"].allowed is True


def _failing(handler_response: httpx.Response | Exception) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if isinstance(handler_response, Exception):
            raise handler_response
        return handler_response

    return httpx.Client(base_url="http://registry.test", transport=httpx.MockTransport(handler))


def test_unreachable_registry_blocks_every_server() -> None:
    registry = _failing(httpx.ConnectError("connection refused"))

    verdicts = check_config(AMP_CONFIG, registry)

    assert {v.server for v in verdicts} == {"payments", "notes"}
    assert not any(v.allowed for v in verdicts)


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(500, json={"title": "Internal Server Error"}),
        httpx.Response(200, text="<html>not json</html>"),
        httpx.Response(200, json={"items": []}),
        httpx.Response(200, json={"servers": [{"server": {"packages": [{"identifier": 3}]}}]}),
    ],
    ids=["server-error", "not-json", "no-servers-key", "bad-package"],
)
def test_unusable_registry_reply_blocks_every_server(response: httpx.Response) -> None:
    verdicts = check_config(AMP_CONFIG, _failing(response))

    assert {v.server for v in verdicts} == {"payments", "notes"}
    assert not any(v.allowed for v in verdicts)


def test_server_listed_on_a_later_page_is_allowed() -> None:
    payments = _record(
        "com.examplebank/payments-readonly", "npm", "@examplebank/payments-readonly-mcp"
    )
    other = _record("com.examplebank/other", "npm", "@examplebank/other-mcp")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("cursor") == "page-2":
            return httpx.Response(200, json={"servers": [payments], "metadata": {"count": 1}})
        body = {"servers": [other], "metadata": {"count": 1, "nextCursor": "page-2"}}
        return httpx.Response(200, json=body)

    registry = httpx.Client(base_url="http://registry.test", transport=httpx.MockTransport(handler))

    allowed = {v.server for v in check_config(AMP_CONFIG, registry) if v.allowed}

    assert allowed == {"payments"}


def _config(tmp_path: Path, entry: dict[str, Any]) -> Path:
    config = tmp_path / "amp.json"
    config.write_text(json.dumps({"amp.mcpServers": {"server": entry}}))
    return config


@pytest.mark.parametrize(
    ("entry", "allowed"),
    [
        ({"command": "uvx", "args": ["approved-mcp==1.0"]}, True),
        ({"command": "uvx", "args": ["approved-mcp@1.0"]}, True),
        ({"command": "uvx", "args": ["--from", "approved-mcp", "approved-mcp"]}, True),
        ({"command": "uvx", "args": ["--with", "other-pkg", "approved-mcp"]}, False),
        (
            {"command": "uvx", "args": ["--from", "approved-mcp", "--with", "x", "approved-mcp"]},
            False,
        ),
        ({"command": "uvx", "args": ["--from", "approved-mcp", "other-cmd"]}, False),
        (
            {
                "command": "npx",
                "args": ["-y", "-p", "other-pkg", "@examplebank/payments-readonly-mcp"],
            },
            False,
        ),
        ({"command": "docker", "args": ["run", "-i", "approved-mcp"]}, False),
    ],
    ids=[
        "pypi-eq-version",
        "uvx-at-version",
        "from-same",
        "with-second-package",
        "from-and-with",
        "from-other-command",
        "npx-second-package",
        "docker-blocked",
    ],
)
def test_runner_arguments_cannot_bring_in_an_unlisted_package(
    tmp_path: Path, entry: dict[str, Any], allowed: bool
) -> None:
    listing = _registry(
        _record("com.examplebank/approved", "pypi", "approved-mcp"),
        _record("com.examplebank/payments-readonly", "npm", "@examplebank/payments-readonly-mcp"),
    )

    (verdict,) = check_config(_config(tmp_path, entry), listing)

    assert verdict.allowed is allowed
