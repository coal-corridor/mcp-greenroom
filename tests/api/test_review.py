"""Separation of duties (registry spec): a reviewer never decides their own submission."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.api.conftest import DANA, RILEY, SAM, sample


def _submit(client: TestClient, slug: str, headers: dict[str, str]) -> str:
    response = client.post("/submissions", json=sample(slug), headers=headers)
    assert response.status_code == 201, response.text
    submission_id: str = response.json()["submission_id"]
    return submission_id


def _review(client: TestClient, submission_id: str, headers: dict[str, str], **body: Any) -> Any:
    return client.post(f"/submissions/{submission_id}/review", json=body, headers=headers)


def _unchanged(client: TestClient, submission_id: str) -> None:
    status = client.get(f"/submissions/{submission_id}", headers=DANA)
    assert status.status_code == 200, status.text
    assert status.json()["outcome"] == "human_review"
    assert client.get("/v0.1/servers").json()["servers"] == []


@pytest.fixture
def pending(client: TestClient) -> str:
    """ambiguous-exporter 2.0.0, submitted by riley (a reviewer), waiting in human review."""
    submission_id = _submit(client, "ambiguous-exporter", RILEY)
    _unchanged(client, submission_id)
    return submission_id


def test_the_submitter_cannot_approve_their_own_submission(
    client: TestClient, pending: str
) -> None:
    response = _review(client, pending, RILEY, action="approve", note="Looks fine.")

    assert response.status_code == 403, response.text
    assert response.json()["rule_id"] == "review.reviewer_is_submitter"
    _unchanged(client, pending)


def test_an_identity_without_the_reviewer_role_cannot_approve(
    client: TestClient, pending: str
) -> None:
    response = _review(client, pending, DANA, action="approve", note="Looks fine.")

    assert response.status_code == 403, response.text
    assert response.json()["rule_id"] == "review.not_reviewer"
    _unchanged(client, pending)


def test_identity_in_the_body_is_ignored(client: TestClient, pending: str) -> None:
    response = _review(client, pending, RILEY, action="approve", note="ok", reviewer="sam")

    assert response.status_code != 200
    _unchanged(client, pending)


@pytest.mark.parametrize("note", ["", "   "])
def test_an_approval_needs_a_note(client: TestClient, pending: str, note: str) -> None:
    response = _review(client, pending, SAM, action="approve", note=note)

    assert response.status_code == 422, response.text
    assert response.json()["rule_id"] == "review.note_required"
    _unchanged(client, pending)


def test_the_other_reviewer_approves_with_a_note_and_publishes(
    client: TestClient, pending: str
) -> None:
    response = _review(client, pending, SAM, action="approve", note="Egress URL is internal.")

    assert response.status_code == 200, response.text
    assert response.json()["outcome"] == "approved"
    assert response.json()["decided_by"] == "sam"
    status = client.get(f"/submissions/{pending}", headers=DANA).json()
    assert status["outcome"] == "approved"
    listed = client.get("/v0.1/servers").json()["servers"]
    assert [entry["server"]["name"] for entry in listed] == ["com.examplebank/ambiguous-exporter"]


def test_a_decline_is_final_and_publishes_nothing(client: TestClient, pending: str) -> None:
    response = _review(client, pending, SAM, action="decline", note="Egress is too broad.")

    assert response.status_code == 200, response.text
    assert response.json()["outcome"] == "rejected"
    assert client.get("/v0.1/servers").json()["servers"] == []
    again = _review(client, pending, SAM, action="approve", note="Changed my mind.")
    assert again.status_code == 409
    assert again.json()["rule_id"] == "review.not_pending"


def test_a_policy_decision_cannot_be_reviewed(client: TestClient) -> None:
    approved = _submit(client, "payments-readonly", DANA)

    response = _review(client, approved, SAM, action="decline", note="No.")

    assert response.status_code == 409
    assert response.json()["rule_id"] == "review.not_pending"


def test_an_unknown_submission_is_404(client: TestClient) -> None:
    response = _review(client, "no-such-id", SAM, action="approve", note="ok")

    assert response.status_code == 404
    assert response.json()["rule_id"] == "submission.not_found"
    assert client.get("/submissions/no-such-id", headers=DANA).status_code == 404
