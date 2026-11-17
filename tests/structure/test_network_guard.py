"""The guard in tests/conftest.py turns "no network in tests" into a check."""

import socket

import httpx
import pytest

from tests.conftest import NetworkBlockedError


def test_connect_to_a_public_address_is_blocked() -> None:
    with (
        socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock,
        pytest.raises(NetworkBlockedError, match="not localhost"),
    ):
        sock.connect(("192.0.2.1", 443))  # TEST-NET-1, never routed


def test_dns_lookup_of_a_public_name_is_blocked() -> None:
    with pytest.raises(NetworkBlockedError, match="DNS lookup"):
        socket.getaddrinfo("example.com", 443)


def test_http_client_call_is_blocked_not_swallowed() -> None:
    with pytest.raises(NetworkBlockedError):
        httpx.get("https://example.com/", timeout=1)


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost"])
def test_localhost_is_allowed(host: str) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port = server.getsockname()[1]
        with socket.create_connection((host, port), timeout=1):
            pass
