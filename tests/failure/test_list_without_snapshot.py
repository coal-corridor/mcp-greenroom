"""Degrade mode, edge case found by the break test: store down from the start, no last-good copy.

The list must say that there is no copy to fall back on, not that nothing can be submitted.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from mcp_greenroom.api.dependencies import get_pipeline
from mcp_greenroom.api.main import create_app
from mcp_greenroom.config import Settings
from tests.fakes import FakePipeline


def test_list_with_no_store_and_no_snapshot_explains_itself(tmp_path: Path) -> None:
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'missing-dir' / 'greenroom.db'}",
        snapshot_path=tmp_path / "none.json",
    )
    app = create_app(settings)
    app.dependency_overrides[get_pipeline] = FakePipeline
    with TestClient(app) as client:
        response = client.get("/v0.1/servers")
    assert response.status_code == 503
    body = response.json()
    assert body["rule_id"] == "store.unavailable"  # stable id, as test_degrade.py pins it
    assert "no last-good copy" in body["message"]
    assert "submitted" not in body["message"]
