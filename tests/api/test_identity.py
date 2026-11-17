"""Identity (parent invariants): from the credential only; stub tokens work only in dev."""

from fastapi.testclient import TestClient

from mcp_greenroom.api.dependencies import get_pipeline
from mcp_greenroom.api.main import create_app
from mcp_greenroom.config import Settings
from tests.api.conftest import DANA, sample
from tests.fakes import FakePipeline


def test_stub_tokens_are_refused_outside_dev(settings: Settings) -> None:
    # config only accepts "dev"; model_copy skips validation to stand in for a later env
    app = create_app(settings.model_copy(update={"env": "prod"}))
    app.dependency_overrides[get_pipeline] = FakePipeline
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/submissions", json=sample("payments-readonly"), headers=DANA)

    assert response.status_code == 401
    assert response.json()["rule_id"] == "auth.unknown_credential"


def test_an_unknown_token_is_refused(client: TestClient) -> None:
    response = client.get("/submissions/x", headers={"Authorization": "Bearer dev-nobody"})

    assert response.status_code == 401
