"""A failed write of the last-good copy is not silent: readiness reports it (review finding 5)."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mcp_greenroom.api.dependencies import get_pipeline
from mcp_greenroom.api.main import create_app
from mcp_greenroom.config import Settings
from tests.api.conftest import DANA, sample
from tests.fakes import FakePipeline


@pytest.fixture
def unwritable(settings: Settings, tmp_path: Path) -> Iterator[TestClient]:
    blocker = tmp_path / "not-a-dir"
    blocker.write_text("a file where the snapshot folder should be")
    app = create_app(settings.model_copy(update={"snapshot_path": blocker / "last-good.json"}))
    app.dependency_overrides[get_pipeline] = FakePipeline
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def test_readiness_reports_a_failed_snapshot_write(unwritable: TestClient) -> None:
    published = unwritable.post("/submissions", json=sample("payments-readonly"), headers=DANA)
    assert published.status_code == 201  # the publish itself stands

    response = unwritable.get("/readyz")

    assert response.status_code == 503
    body = response.json()
    assert body["ready"] is False
    assert "last-good" in body["reason"]


def test_readiness_reports_when_the_last_good_copy_was_written(client: TestClient) -> None:
    client.post("/submissions", json=sample("payments-readonly"), headers=DANA)

    body = client.get("/readyz").json()

    assert body["ready"] is True
    assert body["snapshot_generated_at"]
