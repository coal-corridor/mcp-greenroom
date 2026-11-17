"""The five named samples parse as submissions and, except the unpinned one, fit the schema."""

import json
from pathlib import Path

import jsonschema
import pytest

from mcp_greenroom.models import Submission

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "sample-data" / "servers"
SCHEMA = json.loads((ROOT / "contracts" / "server.schema.json").read_text(encoding="utf-8"))
NAMED = {
    "payments-readonly": "1.2.0",
    "invalid-unpinned": "latest",
    "poisoned-notes": "0.3.1",
    "unrecorded-reporter": "0.1.0",
    "ambiguous-exporter": "2.0.0",
}


def _load(slug: str) -> Submission:
    return Submission.model_validate_json((SAMPLES / f"{slug}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize(("slug", "version"), NAMED.items())
def test_named_sample_is_a_submission(slug: str, version: str) -> None:
    submission = _load(slug)
    assert submission.name == f"com.examplebank/{slug}"
    assert submission.version == version
    assert submission.tools


@pytest.mark.parametrize("slug", [s for s in NAMED if s != "invalid-unpinned"])
def test_server_part_fits_the_pinned_schema(slug: str) -> None:
    jsonschema.Draft7Validator(SCHEMA).validate(_load(slug).server)


def test_unpinned_sample_breaks_the_schema_only_on_the_package_version() -> None:
    # The schema refuses "latest" on packages[].version but accepts it on the top-level
    # version, so vetting needs its own rule for the top level.
    errors = list(jsonschema.Draft7Validator(SCHEMA).iter_errors(_load("invalid-unpinned").server))
    assert [list(e.absolute_path) for e in errors] == [["packages", 0, "version"]]
