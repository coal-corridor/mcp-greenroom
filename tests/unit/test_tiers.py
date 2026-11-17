"""Tiers: high is code execution, credential access, or local read with network egress.
Medium is local write or network egress. Everything else is low."""

import pytest

from mcp_greenroom.models import Capability as C
from mcp_greenroom.models import Tier
from mcp_greenroom.risk.tiers import tier_for


@pytest.mark.parametrize(
    ("capabilities", "tier"),
    [
        (set(), Tier.LOW),
        ({C.LOCAL_READ}, Tier.LOW),
        ({C.LOCAL_WRITE}, Tier.MEDIUM),
        ({C.NETWORK_EGRESS}, Tier.MEDIUM),
        ({C.LOCAL_WRITE, C.NETWORK_EGRESS}, Tier.MEDIUM),
        ({C.CODE_EXEC}, Tier.HIGH),
        ({C.CREDENTIAL_ACCESS}, Tier.HIGH),
        ({C.LOCAL_READ, C.NETWORK_EGRESS}, Tier.HIGH),
        ({C.LOCAL_READ, C.LOCAL_WRITE}, Tier.MEDIUM),
        (set(C), Tier.HIGH),
    ],
)
def test_the_tier_of_a_set_of_capabilities(capabilities: set[C], tier: Tier) -> None:
    assert tier_for(capabilities) is tier
