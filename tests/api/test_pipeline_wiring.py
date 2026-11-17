"""Integration: get_pipeline serves the real pipeline, built once at startup and reused.

Main path (parent spec): payments-readonly 1.2.0 is approved by policy, tier low, inside the
request and in under 5 s, with no dependency override.
"""

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mcp_greenroom.api import main as api_main
from mcp_greenroom.config import Settings
from mcp_greenroom.vetting import factory
from mcp_greenroom.vetting.pipeline import VettingPipeline
from tests.api.conftest import DANA, ROOT, sample


@pytest.fixture
def real_settings(tmp_path: Path) -> Settings:
    return Settings(  # type: ignore[call-arg]
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'greenroom.db'}",
        snapshot_path=tmp_path / "last-good.json",
        recordings_dir=ROOT / "evals" / "recordings",
    )


def test_the_pipeline_is_built_once_at_startup_and_reused(
    real_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    built: list[VettingPipeline] = []

    def counting_build(settings: Settings) -> VettingPipeline:
        pipeline = factory.build_pipeline(settings)
        built.append(pipeline)
        return pipeline

    monkeypatch.setattr(api_main, "build_pipeline", counting_build, raising=False)
    app = api_main.create_app(real_settings)
    with TestClient(app) as client:
        assert len(built) == 1, "build_pipeline must run once, at startup"
        for slug in ("payments-readonly", "unrecorded-reporter"):
            assert client.post("/submissions", json=sample(slug), headers=DANA).status_code < 500
    assert len(built) == 1, "requests must reuse the pipeline built at startup"
    assert app.state.pipeline is built[0]


def test_main_path_through_the_real_pipeline(real_settings: Settings) -> None:
    with TestClient(api_main.create_app(real_settings)) as client:
        started = time.perf_counter()
        response = client.post("/submissions", json=sample("payments-readonly"), headers=DANA)
        elapsed = time.perf_counter() - started
        assert response.status_code == 201, response.text
        body = response.json()
        assert (body["outcome"], body["tier"]) == ("approved", "low")
        assert body["reasons"]
        assert elapsed < 5.0
        listed = client.get("/v0.1/servers").json()["servers"]
        assert [s["server"]["name"] for s in listed] == ["com.examplebank/payments-readonly"]
