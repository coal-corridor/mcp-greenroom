"""Policy constants are tied to the policy version they were decided under."""

from mcp_greenroom.config import Settings
from mcp_greenroom.vetting.policy import ALLOWED_SOURCES, POLICY_VERSION_OF_CONSTANTS


def test_the_constants_belong_to_the_default_policy_version() -> None:
    # A change to a policy constant needs a new policy version, agreed with the user.
    assert Settings.model_fields["policy_version"].default == POLICY_VERSION_OF_CONSTANTS


def test_the_allowed_sources_are_the_strict_list() -> None:
    assert dict(ALLOWED_SOURCES) == {
        "npm": "https://registry.npmjs.org",
        "pypi": "https://pypi.org",
    }
