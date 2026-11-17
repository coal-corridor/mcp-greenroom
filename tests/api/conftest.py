"""An app on a temporary SQLite file and snapshot, with the fake pipeline swapped in."""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from mcp_greenroom.api.dependencies import get_pipeline
from mcp_greenroom.api.main import create_app
from mcp_greenroom.config import Settings
from tests.fakes import FakePipeline

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "sample-data" / "servers"

DANA = {"Authorization": "Bearer dev-dana"}  # submitter only
RILEY = {"Authorization": "Bearer dev-riley"}  # submitter and reviewer
SAM = {"Authorization": "Bearer dev-sam"}  # submitter and reviewer


def sample(slug: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((SAMPLES / f"{slug}.json").read_text(encoding="utf-8"))
    return data


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(  # type: ignore[call-arg]
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'greenroom.db'}",
        snapshot_path=tmp_path / "snapshots" / "last-good.json",
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    app = create_app(settings)
    app.dependency_overrides[get_pipeline] = FakePipeline
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
