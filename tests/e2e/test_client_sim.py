"""Client check (edge.md): the simulator allows listed servers and blocks the rest."""

from pathlib import Path
from typing import Any

import httpx

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
