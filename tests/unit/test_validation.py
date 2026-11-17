"""Decision order step 1: each validation rule refuses with a stable rule id (422)."""

import pytest

from mcp_greenroom.interfaces import Refusal
from mcp_greenroom.vetting.validation import validate
from tests.unit.helpers import load_sample, with_package, with_server, with_tools

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


@pytest.mark.parametrize(
    ("changes", "where"),
    [
        ({"description": None}, "/"),
        ({"name": "no-slash-here"}, "/name"),
        ({"name": "com.examplebank/a/b"}, "/name"),
        ({"version": 120}, "/version"),
        ({"packages": "npm"}, "/packages"),
    ],
)
def test_a_manifest_that_breaks_the_schema_is_refused(
    changes: dict[str, object], where: str
) -> None:
    with pytest.raises(Refusal) as refused:
        validate(with_server(**changes))
    assert refused.value.rule_id == "validation.schema"
    assert f"at {where}" in refused.value.message


def test_a_package_without_transport_is_refused_by_the_schema() -> None:
    with pytest.raises(Refusal) as refused:
        validate(with_package(transport=None))
    assert refused.value.rule_id == "validation.schema"
    assert "at /packages/0" in refused.value.message


def test_the_schema_refusal_escapes_and_truncates_what_it_received() -> None:
    hostile = "com.examplebank/notes‮" + "x" * 300
    with pytest.raises(Refusal) as refused:
        validate(with_server(name=hostile))
    received = refused.value.received
    assert received.isascii()
    assert "\\u202e" in received
    assert len(received) < 100
    assert refused.value.message.startswith("Server manifest does not fit the schema")


@pytest.mark.parametrize(
    "slug", ["payments-readonly", "poisoned-notes", "unrecorded-reporter", "ambiguous-exporter"]
)
def test_the_valid_samples_pass(slug: str) -> None:
    validate(load_sample(slug))


@pytest.mark.parametrize(
    "changes",
    [
        {"registryType": "oci", "registryBaseUrl": "https://docker.io"},
        {"registryType": "mcpb", "registryBaseUrl": "https://github.com"},
        {"registryBaseUrl": "https://npm.mirror.example"},
        {"registryBaseUrl": "http://registry.npmjs.org"},
        {"registryType": "pypi", "registryBaseUrl": "https://registry.npmjs.org"},
        {"identifier": "https://github.com/examplebank/releases/download/v1/pkg.tgz"},
    ],
)
def test_a_package_from_a_source_not_allowed_is_refused(changes: dict[str, str]) -> None:
    with pytest.raises(Refusal) as refused:
        validate(with_package(**changes))
    assert refused.value.rule_id == "validation.source_not_allowed"
    assert refused.value.message.startswith("Package source is not allowed")


@pytest.mark.parametrize("packages", [None, []])
def test_a_server_with_no_package_is_refused_as_source_not_allowed(packages: object) -> None:
    with pytest.raises(Refusal) as refused:
        validate(with_server(packages=packages))
    assert refused.value.rule_id == "validation.source_not_allowed"


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"registryBaseUrl": None},
        {"registryBaseUrl": "https://registry.npmjs.org/"},
        {"registryType": "pypi", "registryBaseUrl": "https://pypi.org", "identifier": "eb-mcp"},
        {"registryType": "pypi", "registryBaseUrl": None, "identifier": "eb-mcp"},
    ],
)
def test_a_package_from_an_allowed_source_passes(changes: dict[str, str]) -> None:
    validate(with_package(**changes))


def test_a_submission_with_no_tools_is_refused() -> None:
    with pytest.raises(Refusal) as refused:
        validate(with_tools([]))
    assert refused.value.rule_id == "validation.no_tools"
    assert refused.value.message.startswith("No tools")


@pytest.mark.parametrize("kind", ["streamable-http", "sse"])
def test_a_server_with_remotes_is_refused_as_source_not_allowed(kind: str) -> None:
    remote = [{"type": kind, "url": "https://mcp.elsewhere.example/mcp"}]
    with pytest.raises(Refusal) as refused:
        validate(with_server(remotes=remote))
    assert refused.value.rule_id == "validation.source_not_allowed"
    assert "remote" in refused.value.message


@pytest.mark.parametrize(
    "identifier",
    [
        "github:examplebank/notes-mcp",
        "examplebank/notes-mcp",
        "file:../notes-mcp",
        "git@git.example.com:examplebank/notes-mcp.git",
        "git+https://git.example.com/examplebank/notes-mcp.git",
        "@examplebank/notes-mcp@1.0.0",
        "notes-mcp@latest",
        "./notes-mcp.tgz",
        "Notes-MCP",
        "",
    ],
)
def test_an_npm_identifier_outside_the_name_grammar_is_refused(identifier: str) -> None:
    with pytest.raises(Refusal) as refused:
        validate(with_package(identifier=identifier))
    assert refused.value.rule_id in {"validation.source_not_allowed", "validation.schema"}


@pytest.mark.parametrize(
    "identifier",
    [
        "eb-mcp @ https://files.example.com/eb_mcp-1.0.0.whl",
        "git+https://git.example.com/eb-mcp.git",
        "eb-mcp==1.0.0",
        "eb-mcp[extra]",
        "./eb_mcp",
        "-eb-mcp",
    ],
)
def test_a_pypi_identifier_outside_the_name_grammar_is_refused(identifier: str) -> None:
    with pytest.raises(Refusal) as refused:
        validate(with_package(registryType="pypi", registryBaseUrl=None, identifier=identifier))
    assert refused.value.rule_id == "validation.source_not_allowed"


@pytest.mark.parametrize(
    ("registry", "identifier"),
    [
        ("npm", "@examplebank/payments-readonly-mcp"),
        ("npm", "notes-mcp"),
        ("npm", "notes.mcp_v2"),
        ("pypi", "eb-mcp"),
        ("pypi", "Eb_MCP.server2"),
    ],
)
def test_a_plain_package_name_passes(registry: str, identifier: str) -> None:
    validate(with_package(registryType=registry, registryBaseUrl=None, identifier=identifier))
