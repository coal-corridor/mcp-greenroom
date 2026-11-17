"""Immutable versions (parent spec): same content returns the stored decision, other content 409."""

import pytest
from fastapi.testclient import TestClient

from tests.api.conftest import DANA, SAM, sample


@pytest.mark.parametrize("slug", ["payments-readonly", "ambiguous-exporter", "poisoned-notes"])
def test_identical_content_returns_the_existing_decision(client: TestClient, slug: str) -> None:
    first = client.post("/submissions", json=sample(slug), headers=DANA)
    assert first.status_code == 201, first.text

    again = client.post("/submissions", json=sample(slug), headers=SAM)

    assert again.status_code == 200, again.text
    assert again.json() == first.json()


def test_identical_content_is_not_vetted_again(client: TestClient) -> None:
    client.post("/submissions", json=sample("payments-readonly"), headers=DANA)
    client.post("/submissions", json=sample("payments-readonly"), headers=DANA)

    assert len(client.get("/v0.1/servers").json()["servers"]) == 1


@pytest.mark.parametrize("slug", ["payments-readonly", "ambiguous-exporter", "poisoned-notes"])
def test_other_content_under_a_decided_version_is_refused_with_409(
    client: TestClient, slug: str
) -> None:
    original = sample(slug)
    assert client.post("/submissions", json=original, headers=DANA).status_code == 201

    changed_manifest = {**original, "server": {**original["server"], "title": "Changed"}}
    changed_tool = {
        **original,
        "tools": [{**original["tools"][0], "description": "Something else."}]
        + original["tools"][1:],
    }
    for body in (changed_manifest, changed_tool):
        response = client.post("/submissions", json=body, headers=DANA)
        assert response.status_code == 409, response.text
        assert response.json()["rule_id"] == "submission.version_exists"
        assert response.json()["message"]
