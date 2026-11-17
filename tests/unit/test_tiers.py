"""Tiers: high is code execution, credential access, or local read with network egress.
Medium is local write or network egress. Everything else is low."""

import pytest

from mcp_greenroom.models import Capability as Cap
from mcp_greenroom.models import Tier
from mcp_greenroom.risk.tiers import tier_for


@pytest.mark.parametrize(
    ("capabilities", "tier"),
    [
        (set(), Tier.LOW),
        ({Cap.LOCAL_READ}, Tier.LOW),
        ({Cap.LOCAL_WRITE}, Tier.MEDIUM),
        ({Cap.NETWORK_EGRESS}, Tier.MEDIUM),
        ({Cap.LOCAL_WRITE, Cap.NETWORK_EGRESS}, Tier.MEDIUM),
        ({Cap.CODE_EXEC}, Tier.HIGH),
        ({Cap.CREDENTIAL_ACCESS}, Tier.HIGH),
        ({Cap.LOCAL_READ, Cap.NETWORK_EGRESS}, Tier.HIGH),
        ({Cap.LOCAL_READ, Cap.LOCAL_WRITE}, Tier.MEDIUM),
        (set(Cap), Tier.HIGH),
    ],
)
def test_the_tier_of_a_set_of_capabilities(capabilities: set[Cap], tier: Tier) -> None:
    assert tier_for(capabilities) is tier
