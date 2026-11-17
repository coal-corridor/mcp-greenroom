"""Policy constants. Each belongs to the policy version that set it.

POLICY_VERSION_OF_CONSTANTS is the policy version (config.Settings.policy_version) under
which these values were decided. Changing a value here is a policy change: it needs a new
policy version, agreed with the user. tests/unit/test_policy.py pins the pair.
"""

from types import MappingProxyType

POLICY_VERSION_OF_CONSTANTS = "2026-11-17.1"

# Allowed package sources: registry type -> its one allowed base URL. A package without
# registryBaseUrl comes from the type's public registry. Anything else is refused (422).
# Roadmap: allowed sources as a setting.
ALLOWED_SOURCES: MappingProxyType[str, str] = MappingProxyType(
    {
        "npm": "https://registry.npmjs.org",
        "pypi": "https://pypi.org",
    }
)

# Arguments and environment variables that point an installer at another registry. A list
# cannot be complete (roadmap: build the install command ourselves, ignore submitted ones).
REGISTRY_OVERRIDE_FLAGS = frozenset(
    {"--registry", "--index-url", "-i", "--extra-index-url", "--find-links", "-f", "--index"}
)
REGISTRY_OVERRIDE_VARIABLES = frozenset(
    {
        "NPM_CONFIG_REGISTRY",
        "PIP_INDEX_URL",
        "PIP_EXTRA_INDEX_URL",
        "PIP_FIND_LINKS",
        "UV_INDEX_URL",
    }
)
