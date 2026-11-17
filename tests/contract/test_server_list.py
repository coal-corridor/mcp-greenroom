"""Standard format (registry spec): GET /v0.1/servers validates against the pinned OpenAPI."""

from pathlib import Path
from typing import Any

import jsonschema
import yaml
from fastapi.testclient import TestClient

from tests.api.conftest import DANA, RILEY, sample

ROOT = Path(__file__).resolve().parents[2]
OPENAPI = yaml.safe_load((ROOT / "contracts" / "registry-openapi.yaml").read_text(encoding="utf-8"))
# Greenroom's own fields. None of them may reach the published list.
OWN_KEYS = {
    "outcome",
    "tier",
    "reasons",
    "findings",
    "risks",
    "policy_version",
    "decided_by",
    "submission_id",
    "submitted_by",
    "note",
    "notes",
    "tools",
}


def _validate(body: dict[str, Any]) -> None:
    schema = {"$ref": "#/components/schemas/ServerList", "components": OPENAPI["components"]}
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER
    )
    errors = sorted(validator.iter_errors(body), key=lambda e: list(e.path))
    assert not errors, [f"{list(e.path)}: {e.message}" for e in errors]


def _keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {k for v in value.values() for k in _keys(v)}
    if isinstance(value, list):
        return {k for v in value for k in _keys(v)}
    return set()


def test_empty_list_validates(client: TestClient) -> None:
    response = client.get("/v0.1/servers")
    assert response.status_code == 200, response.text
    _validate(response.json())
    assert response.json()["servers"] == []


def test_list_holds_only_approved_versions_in_upstream_format(client: TestClient) -> None:
    approved = sample("payments-readonly")
    client.post("/submissions", json=approved, headers=DANA)
    client.post("/submissions", json=sample("ambiguous-exporter"), headers=RILEY)  # human review
    client.post("/submissions", json=sample("poisoned-notes"), headers=DANA)  # rejected

    response = client.get("/v0.1/servers")

    assert response.status_code == 200, response.text
    body = response.json()
    _validate(body)
    assert [entry["server"] for entry in body["servers"]] == [approved["server"]]
    official = body["servers"][0]["_meta"]["io.modelcontextprotocol.registry/official"]
    assert official["status"] == "active"
    assert not _keys(body) & OWN_KEYS


def test_list_pages_with_a_cursor(client: TestClient) -> None:
    base = sample("payments-readonly")
    versions = ["1.2.0", "1.2.1", "1.3.0"]
    for version in versions:
        payload = {**base, "server": {**base["server"], "version": version}}
        assert client.post("/submissions", json=payload, headers=DANA).status_code == 201

    seen: list[str] = []
    cursor: str | None = None
    for _ in range(len(versions) + 1):
        params: dict[str, Any] = {"limit": 2} | ({"cursor": cursor} if cursor else {})
        body = client.get("/v0.1/servers", params=params).json()
        _validate(body)
        assert len(body["servers"]) <= 2
        seen += [entry["server"]["version"] for entry in body["servers"]]
        cursor = body.get("metadata", {}).get("nextCursor")
        if not cursor:
            break
    assert seen == versions
