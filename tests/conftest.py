"""Shared test setup.

Network guard: any outbound connection, or DNS lookup, to a host other than
localhost fails the test. Tests use the fakes under tests/, never a live call.
The guard is installed in pytest_configure, so imports at collection time are
covered too.
"""

from __future__ import annotations

import ipaddress
import socket
from typing import Any

import pytest

_LOCAL_NAMES = {"localhost", "localhost.localdomain", "ip6-localhost", ""}


class NetworkBlockedError(RuntimeError):
    """Raised for an outbound connection in a test.

    Deliberately not an OSError, so code that degrades on connection errors
    cannot swallow it and let the test pass.
    """


def _is_local(host: object) -> bool:
    if host is None:
        return True
    if isinstance(host, bytes):
        host = host.decode(errors="replace")
    if not isinstance(host, str):
        return False
    name = host.strip("[]").split("%", 1)[0].lower()
    if name in _LOCAL_NAMES:
        return True
    try:
        return ipaddress.ip_address(name).is_loopback
    except ValueError:
        return False


def _blocked(what: str, target: object) -> NetworkBlockedError:
    return NetworkBlockedError(
        f"Network call blocked in tests: {what}. "
        f"Received target {target!r}, which is not localhost. "
        "Use a fake from tests/ instead of a live call."
    )


_real_connect = socket.socket.connect
_real_connect_ex = socket.socket.connect_ex
_real_getaddrinfo = socket.getaddrinfo


def _guarded_connect(self: socket.socket, address: Any) -> None:
    if self.family in (socket.AF_INET, socket.AF_INET6) and not _is_local(address[0]):
        raise _blocked("socket connect", address)
    _real_connect(self, address)


def _guarded_connect_ex(self: socket.socket, address: Any) -> int:
    if self.family in (socket.AF_INET, socket.AF_INET6) and not _is_local(address[0]):
        raise _blocked("socket connect_ex", address)
    return _real_connect_ex(self, address)


def _guarded_getaddrinfo(host: Any, *args: Any, **kwargs: Any) -> Any:
    if not _is_local(host):
        raise _blocked("DNS lookup", host)
    return _real_getaddrinfo(host, *args, **kwargs)


def pytest_configure(config: pytest.Config) -> None:
    socket.socket.connect = _guarded_connect  # type: ignore[method-assign]
    socket.socket.connect_ex = _guarded_connect_ex  # type: ignore[method-assign]
    socket.getaddrinfo = _guarded_getaddrinfo


def pytest_unconfigure(config: pytest.Config) -> None:
    socket.socket.connect = _real_connect  # type: ignore[method-assign]
    socket.socket.connect_ex = _real_connect_ex  # type: ignore[method-assign]
    socket.getaddrinfo = _real_getaddrinfo
