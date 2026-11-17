"""Injection points. Tests swap each one through app.dependency_overrides.

Frozen names and return types. Registry writes the bodies; until then each raises.
Example in a test:

    app.dependency_overrides[get_pipeline] = lambda: FakePipeline()
"""

from mcp_greenroom.interfaces import Pipeline, Store
from mcp_greenroom.models import Identity


def get_pipeline() -> Pipeline:
    """The vetting pipeline, with its classifier provider and scanner already inside."""
    raise NotImplementedError("registry wires the real pipeline here")


def get_store() -> Store:
    """The store. Registry defines its methods."""
    raise NotImplementedError("registry wires the store here")


def get_identity() -> Identity:
    """The caller, from the credential (bearer token), never from the request body.

    Unknown or missing token: 401. Dev stub tokens are in mcp_greenroom.config.DEV_IDENTITIES.
    """
    raise NotImplementedError("registry resolves the identity here")
