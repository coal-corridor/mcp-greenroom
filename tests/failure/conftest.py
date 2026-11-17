"""Reuse the app fixtures of tests/api."""

from tests.api.conftest import client, settings

__all__ = ["client", "settings"]
