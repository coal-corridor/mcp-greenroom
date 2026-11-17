"""CLI submit (edge.md): exit code per outcome, --json, errors. API answers are canned.

Bodies follow POST /submissions on area/registry (SubmissionResult: the Decision plus
submission_id, name, version, submitted_by), built from the contracts FakePipeline.
"""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from typer.testing import CliRunner

from mcp_greenroom import cli
from mcp_greenroom.cli import app
from mcp_greenroom.models import Submission
from tests.fakes import FakePipeline

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "sample-data" / "servers"

runner = CliRunner()


def result_body(sample: str) -> dict[str, Any]:
    submission = Submission.model_validate_json((SAMPLES / f"{sample}.json").read_text())
    decision = FakePipeline().vet(submission)
    return {
        **decision.model_dump(mode="json"),
        "submission_id": f"sub-{sample}",
        "name": submission.name,
        "version": submission.version,
        "submitted_by": "dana",
    }


def api_answering(status: int, body: Any) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/submissions"
        assert request.headers["authorization"] == "Bearer dev-dana"
        return httpx.Response(status, json=body)

    return httpx.MockTransport(handler)


def submit(sample: str, *extra: str) -> Any:
    args = ["submit", str(SAMPLES / f"{sample}.json"), "--api", "http://api.test"]
    return runner.invoke(app, [*args, "--token", "dev-dana", *extra])


@pytest.mark.parametrize(
    ("sample", "code", "word"),
    [
        ("payments-readonly", 0, "✓ approved"),
        ("ambiguous-exporter", 10, "! needs review"),
        ("poisoned-notes", 20, "✗ rejected"),
    ],
)
def test_submit_exit_code_and_status_word_per_outcome(
    monkeypatch: pytest.MonkeyPatch, sample: str, code: int, word: str
) -> None:
    monkeypatch.setattr(cli, "TRANSPORT", api_answering(201, result_body(sample)))

    result = submit(sample)

    assert result.exit_code == code, result.output
    assert word in result.stdout
    assert (
        json.loads((SAMPLES / f"{sample}.json").read_text())["server"]["version"] in result.stdout
    )


@pytest.mark.parametrize("sample", ["payments-readonly", "poisoned-notes"])
def test_submit_json_prints_the_api_body_and_nothing_else(
    monkeypatch: pytest.MonkeyPatch, sample: str
) -> None:
    body = result_body(sample)
    monkeypatch.setattr(cli, "TRANSPORT", api_answering(201, body))

    result = submit(sample, "--json")

    assert json.loads(result.stdout) == body
    assert result.exit_code == {"payments-readonly": 0, "poisoned-notes": 20}[sample]
