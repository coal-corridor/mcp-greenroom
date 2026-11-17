"""Main path (parent spec): payments-readonly 1.2.0 is approved by policy inside the request."""

import time

from fastapi.testclient import TestClient

from tests.api.conftest import DANA, sample


def test_benign_server_is_approved_by_policy_inside_the_request(client: TestClient) -> None:
    started = time.monotonic()
    response = client.post("/submissions", json=sample("payments-readonly"), headers=DANA)
    elapsed = time.monotonic() - started

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["outcome"] == "approved"
    assert body["tier"] == "low"
    assert body["decided_by"] == "policy"
    assert body["reasons"], "an approval carries its reasons"
    assert body["name"] == "com.examplebank/payments-readonly"
    assert body["version"] == "1.2.0"
    assert body["submission_id"]
    assert elapsed < 5.0
