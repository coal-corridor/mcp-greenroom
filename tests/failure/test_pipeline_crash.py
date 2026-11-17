"""Fail closed: a pipeline that raises anyway gives a clean 500 and stores nothing."""

from fastapi.testclient import TestClient

from mcp_greenroom.api.dependencies import get_pipeline
from mcp_greenroom.models import Decision, Submission
from tests.api.conftest import DANA, sample


class CrashingPipeline:
    def vet(self, submission: Submission) -> Decision:
        raise RuntimeError("boom at /secret/path.py line 42")


def test_a_crashing_pipeline_approves_nothing_and_shows_no_trace(client: TestClient) -> None:
    client.app.dependency_overrides[get_pipeline] = CrashingPipeline  # type: ignore[attr-defined]

    response = client.post("/submissions", json=sample("payments-readonly"), headers=DANA)

    assert response.status_code == 500
    assert response.json()["rule_id"] == "internal.error"
    assert "boom" not in response.text
    assert "Traceback" not in response.text
    assert client.get("/v0.1/servers").json()["servers"] == []


def test_a_crash_stores_no_decision(client: TestClient) -> None:
    from tests.fakes import FakePipeline

    client.app.dependency_overrides[get_pipeline] = CrashingPipeline  # type: ignore[attr-defined]
    client.post("/submissions", json=sample("payments-readonly"), headers=DANA)
    client.app.dependency_overrides[get_pipeline] = FakePipeline  # type: ignore[attr-defined]

    response = client.post("/submissions", json=sample("payments-readonly"), headers=DANA)

    assert response.status_code == 201
