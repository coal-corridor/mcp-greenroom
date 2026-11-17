"""Decision order step 1: each validation rule refuses with a stable rule id (422)."""

import pytest

from mcp_greenroom.interfaces import Refusal
from mcp_greenroom.vetting.validation import validate
from tests.unit.helpers import load_sample, with_package, with_server

NOT_PINNED = [
    "latest",
    "LATEST",
    "next",
    "^1.2.3",
    "~1.2.3",
    ">=1.2.3",
    "1.x",
    "1.*",
    "*",
    "",
    " 1.2.0",
    "1.2.0 || 2.0.0",
]
PINNED = ["1.2.0", "0.3.1", "2.1.0-alpha.1", "1.0.0+build.7", "2024.11.17", "v1.2.0"]


def test_the_unpinned_sample_is_refused_as_not_pinned() -> None:
    with pytest.raises(Refusal) as refused:
        validate(load_sample("invalid-unpinned"))
    assert refused.value.rule_id == "validation.version_not_pinned"
    assert refused.value.received == "'latest'"


@pytest.mark.parametrize("version", NOT_PINNED)
def test_an_unpinned_server_version_is_refused(version: str) -> None:
    with pytest.raises(Refusal) as refused:
        validate(with_server(version=version))
    assert refused.value.rule_id == "validation.version_not_pinned"


@pytest.mark.parametrize("version", NOT_PINNED)
def test_an_unpinned_package_version_is_refused(version: str) -> None:
    with pytest.raises(Refusal) as refused:
        validate(with_package(version=version))
    assert refused.value.rule_id == "validation.version_not_pinned"


@pytest.mark.parametrize("version", PINNED)
def test_an_exact_version_passes(version: str) -> None:
    validate(with_server(version=version))
    validate(with_package(version=version))


def test_the_refusal_says_what_failed_what_was_received_and_what_to_do() -> None:
    with pytest.raises(Refusal) as refused:
        validate(with_server(version="^1.2.3"))
    message = refused.value.message
    assert message.startswith("Version is not pinned")
    assert "Received '^1.2.3'" in message
    assert "Submit" in message
