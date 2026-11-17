"""Validation rejection (parent spec): 422, stable rule id, readable message, nothing stored."""

from fastapi.testclient import TestClient

from tests.api.conftest import DANA, sample


def _assert_clean_error(text: str) -> None:
    assert "Traceback" not in text
    assert 'File "' not in text


def test_unpinned_version_is_refused_with_a_rule_id(client: TestClient) -> None:
    response = client.post("/submissions", json=sample("invalid-unpinned"), headers=DANA)

    assert response.status_code == 422, response.text
    body = response.json()
    assert body["rule_id"] == "fake.version_not_pinned"
    assert body["message"]
    assert body["received"] == "latest"
    _assert_clean_error(response.text)
    assert client.get("/v0.1/servers").json()["servers"] == []


def test_a_refusal_stores_no_decision(client: TestClient) -> None:
    refused = sample("invalid-unpinned")
    assert client.post("/submissions", json=refused, headers=DANA).status_code == 422

    fixed = {**refused, "server": {**refused["server"], "version": "1.0.0"}}
    response = client.post("/submissions", json=fixed, headers=DANA)

    assert response.status_code == 201, response.text


def test_a_body_that_is_not_a_submission_is_refused_with_a_rule_id(client: TestClient) -> None:
    response = client.post("/submissions", json={"server": "nope"}, headers=DANA)

    assert response.status_code == 422, response.text
    assert response.json()["rule_id"] == "validation.malformed"
    _assert_clean_error(response.text)


def test_a_missing_credential_is_refused_with_401(client: TestClient) -> None:
    response = client.post("/submissions", json=sample("payments-readonly"))

    assert response.status_code == 401
    assert response.json()["rule_id"] == "auth.unknown_credential"
