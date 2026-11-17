"""Degrade mode (registry spec): the database is broken at the store, not by a handler flag."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mcp_greenroom.config import Settings
from tests.api.conftest import DANA, RILEY, SAM, sample
from tests.contract.test_server_list import _validate


def _break_database(settings: Settings) -> None:
    """Overwrite the SQLite file with bytes that are not a database."""
    path = Path(settings.database_url.removeprefix("sqlite:///"))
    assert path.exists()
    path.write_bytes(b"this is not a sqlite database\n" * 512)


@pytest.fixture
def approved(client: TestClient) -> dict[str, object]:
    response = client.post("/submissions", json=sample("payments-readonly"), headers=DANA)
    assert response.status_code == 201, response.text
    body: dict[str, object] = client.get("/v0.1/servers").json()
    assert len(body["servers"]) == 1  # type: ignore[arg-type]
    return body


def test_ready_when_the_store_answers(client: TestClient) -> None:
    assert client.get("/livez").status_code == 200
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["ready"] is True


def test_the_last_published_list_is_served_marked_degraded(
    client: TestClient, settings: Settings, approved: dict[str, object]
) -> None:
    _break_database(settings)

    response = client.get("/v0.1/servers")

    assert response.status_code == 200, response.text
    assert response.headers["X-Greenroom-Degraded"] == "true"
    assert response.headers["X-Greenroom-Generated-At"]
    assert response.json()["servers"] == approved["servers"]
    _validate(response.json())


def test_a_healthy_list_is_not_marked_degraded(
    client: TestClient, approved: dict[str, object]
) -> None:
    response = client.get("/v0.1/servers")

    assert "X-Greenroom-Degraded" not in response.headers


def test_new_submissions_are_refused_with_503(
    client: TestClient, settings: Settings, approved: dict[str, object]
) -> None:
    _break_database(settings)

    response = client.post("/submissions", json=sample("ambiguous-exporter"), headers=RILEY)

    assert response.status_code == 503, response.text
    assert response.json()["rule_id"] == "store.unavailable"
    assert "Traceback" not in response.text


def test_reviews_are_refused_with_503(client: TestClient, settings: Settings) -> None:
    pending = client.post("/submissions", json=sample("ambiguous-exporter"), headers=RILEY)
    _break_database(settings)

    response = client.post(
        f"/submissions/{pending.json()['submission_id']}/review",
        json={"action": "approve", "note": "ok"},
        headers=SAM,
    )

    assert response.status_code == 503
    assert response.json()["rule_id"] == "store.unavailable"


def test_readiness_says_not_ready_and_why(
    client: TestClient, settings: Settings, approved: dict[str, object]
) -> None:
    _break_database(settings)

    response = client.get("/readyz")

    assert response.status_code == 503
    body = response.json()
    assert body["ready"] is False
    assert "store" in body["reason"]
    assert client.get("/livez").status_code == 200


def test_no_list_at_all_without_a_last_good_copy(client: TestClient, settings: Settings) -> None:
    _break_database(settings)

    response = client.get("/v0.1/servers")

    assert response.status_code == 503
    assert response.json()["rule_id"] == "store.unavailable"
