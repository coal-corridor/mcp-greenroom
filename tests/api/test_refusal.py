"""Validation rejection (parent spec): 422, stable rule id, readable message, nothing stored."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from mcp_greenroom.api.dependencies import get_pipeline
from mcp_greenroom.interfaces import Refusal
from mcp_greenroom.models import Decision, Submission
from tests.api.conftest import DANA, sample
from tests.fakes import FakePipeline


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


class RefuseOncePipeline:
    """Refuses its first submission (a pinned version), then answers like the fake."""

    def __init__(self) -> None:
        self.fake = FakePipeline()
        self.refused = False

    def vet(self, submission: Submission) -> Decision:
        if not self.refused:
            self.refused = True
            raise Refusal("fake.no_tools", "Submission has no tools.", "[]")
        return self.fake.vet(submission)


def test_a_refusal_stores_no_decision(client: TestClient) -> None:
    pipeline = RefuseOncePipeline()
    client.app.dependency_overrides[get_pipeline] = lambda: pipeline  # type: ignore[attr-defined]
    body = sample("payments-readonly")  # pinned: 1.2.0

    refused = client.post("/submissions", json=body, headers=DANA)
    assert refused.status_code == 422, refused.text
    refusal_id = refused.json()["submission_id"]

    assert client.get(f"/submissions/{refusal_id}", headers=DANA).status_code == 404
    # the same name and version again: a stored decision would make this a 200 or a 409
    again = client.post("/submissions", json=body, headers=DANA)
    assert again.status_code == 201, again.text
    assert again.json()["submission_id"] != refusal_id


@pytest.mark.parametrize(
    "body",
    [{"server": "nope"}, {"server": {}, "tools": []}, {"server": {"name": "a/b"}, "tools": []}],
)
def test_a_body_that_is_not_a_submission_is_refused_with_a_rule_id(
    client: TestClient, body: dict[str, Any]
) -> None:
    response = client.post("/submissions", json=body, headers=DANA)

    assert response.status_code == 422, response.text
    assert response.json()["rule_id"] == "validation.malformed"
    _assert_clean_error(response.text)


def test_a_missing_credential_is_refused_with_401(client: TestClient) -> None:
    response = client.post("/submissions", json=sample("payments-readonly"))

    assert response.status_code == 401
    assert response.json()["rule_id"] == "auth.unknown_credential"
