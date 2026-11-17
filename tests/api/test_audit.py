"""Audit (registry spec): every decision and every refusal reads back; no update or delete."""

import pytest
import sqlalchemy
from fastapi.testclient import TestClient

from mcp_greenroom.config import Settings
from mcp_greenroom.store import SqlStore
from tests.api.conftest import DANA, RILEY, SAM, sample
from tests.fakes import POLICY_VERSION


def _audit(client: TestClient, submission_id: str) -> list[dict[str, object]]:
    response = client.get(f"/submissions/{submission_id}/audit", headers=DANA)
    assert response.status_code == 200, response.text
    events: list[dict[str, object]] = response.json()["events"]
    return events


@pytest.mark.parametrize("slug", ["payments-readonly", "ambiguous-exporter", "poisoned-notes"])
def test_a_policy_decision_reads_back(client: TestClient, slug: str) -> None:
    submission_id = client.post("/submissions", json=sample(slug), headers=DANA).json()[
        "submission_id"
    ]

    events = _audit(client, submission_id)

    assert [e["action"] for e in events] == ["submitted", "policy_decision"]
    submitted, decided = events
    assert submitted["actor"] == "dana"
    assert decided["actor"] == "policy"
    assert decided["reasons"], "a policy decision carries its reasons"
    for event in events:
        assert event["policy_version"] == POLICY_VERSION
        assert event["at"]


def test_a_human_decision_reads_back(client: TestClient) -> None:
    body = client.post("/submissions", json=sample("ambiguous-exporter"), headers=RILEY).json()
    client.post(
        f"/submissions/{body['submission_id']}/review",
        json={"action": "approve", "note": "Egress is internal."},
        headers=SAM,
    )

    events = _audit(client, body["submission_id"])

    assert [e["action"] for e in events] == ["submitted", "policy_decision", "approved"]
    human = events[-1]
    assert human["actor"] == "sam"
    assert human["reasons"] == [
        {"code": "review.approved", "message": "Egress is internal.", "tool_name": None}
    ]
    assert human["policy_version"] == POLICY_VERSION


def test_a_validation_refusal_leaves_an_audit_event(client: TestClient, settings: Settings) -> None:
    refused = client.post("/submissions", json=sample("invalid-unpinned"), headers=DANA).json()

    events = _audit(client, refused["submission_id"])

    assert [e["action"] for e in events] == ["refused"]
    assert events[0]["actor"] == "dana"
    assert events[0]["policy_version"] == settings.policy_version
    assert events[0]["reasons"][0]["code"] == refused["rule_id"]  # type: ignore[index]


def test_an_unknown_id_has_no_audit(client: TestClient) -> None:
    response = client.get("/submissions/no-such-id/audit", headers=DANA)

    assert response.status_code == 404
    assert response.json()["rule_id"] == "submission.not_found"


def test_the_store_has_no_update_or_delete_for_audit_records() -> None:
    verbs = ("update", "delete", "remove", "edit", "replace", "clear", "truncate")
    methods = [name for name in dir(SqlStore) if not name.startswith("__")]
    assert not [m for m in methods if any(verb in m.lower() for verb in verbs)]


@pytest.mark.parametrize(
    "statement", ["UPDATE audit_events SET event_json = '{}'", "DELETE FROM audit_events"]
)
def test_the_database_refuses_to_change_audit_records(
    client: TestClient, settings: Settings, statement: str
) -> None:
    client.post("/submissions", json=sample("payments-readonly"), headers=DANA)
    engine = sqlalchemy.create_engine(settings.database_url)

    with (
        pytest.raises(sqlalchemy.exc.DatabaseError, match="append-only"),
        engine.begin() as conn,
    ):
        conn.execute(sqlalchemy.text(statement))
    engine.dispose()
