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
