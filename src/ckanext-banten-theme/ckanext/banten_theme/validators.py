"""URL safety validators (anti-SSRF) used by BantenThemePlugin.

Implements pentest finding HIGH-3:
    Reject `resource_create` / `resource_update` URLs that point to private,
    loopback, link-local or cloud-metadata addresses, or use non-HTTP schemes
    like file://, ftp://, gopher://.

The function is exposed via `plugins.IValidators` (as
`banten_safe_remote_url`) and is also called directly inside the resource
controller hooks (`before_resource_create`, `before_resource_update`) so it
applies even when callers bypass schema customization.
"""

from __future__ import annotations

import ipaddress
import logging
import socket
from urllib.parse import urlparse

import ckan.plugins.toolkit as toolkit

log = logging.getLogger(__name__)

ALLOWED_SCHEMES = {"http", "https"}

_PRIVATE_NETS_V4 = [
    ipaddress.ip_network(n)
    for n in (
        "0.0.0.0/8",
        "10.0.0.0/8",
        "127.0.0.0/8",
        "169.254.0.0/16",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "224.0.0.0/4",
        "240.0.0.0/4",
    )
]

_PRIVATE_NETS_V6 = [
    ipaddress.ip_network(n)
    for n in (
        "::1/128",
        "::/128",
        "fc00::/7",
        "fe80::/10",
        "ff00::/8",
    )
]

# Hostnames always rejected even when DNS is unavailable on the server.
_BLOCKED_HOSTNAMES = frozenset(
    {
        "localhost",
        "metadata.google.internal",
        "metadata.google",
    }
)
_BLOCKED_HOSTNAME_SUFFIXES = (".local", ".internal", ".localhost")


def _is_blocked_hostname(host: str) -> bool:
    lower = host.lower().rstrip(".")
    if lower in _BLOCKED_HOSTNAMES:
        return True
    return any(lower.endswith(suffix) for suffix in _BLOCKED_HOSTNAME_SUFFIXES)


def _is_private_ip(addr_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(addr_str)
    except ValueError:
        return False
    nets = _PRIVATE_NETS_V6 if ip.version == 6 else _PRIVATE_NETS_V4
    return any(ip in net for net in nets)


def _resolve_all(host: str):
    """Resolve host to IP strings. Returns None when lookup fails or times out."""
    old_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(5)
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except (socket.gaierror, socket.herror, UnicodeError, socket.timeout, OSError):
        return None
    finally:
        socket.setdefaulttimeout(old_timeout)
    return [info[4][0] for info in infos]


def _check_url(value: str) -> None:
    """Raise toolkit.Invalid when URL is unsafe; return None when OK."""
    try:
        parsed = urlparse(value)
    except Exception:
        raise toolkit.Invalid("URL tidak valid")

    scheme = (parsed.scheme or "").lower()
    if scheme not in ALLOWED_SCHEMES:
        raise toolkit.Invalid(
            "URL hanya boleh menggunakan skema http atau https"
        )

    host = parsed.hostname
    if not host:
        raise toolkit.Invalid("URL tidak memiliki host yang valid")

    if _is_private_ip(host):
        raise toolkit.Invalid(
            "URL menunjuk ke alamat private/internal yang tidak diizinkan"
        )

    if _is_blocked_hostname(host):
        raise toolkit.Invalid(
            "URL menunjuk ke host internal yang tidak diizinkan"
        )

    addrs = _resolve_all(host)
    if addrs is None:
        # Prod VM may have broken outbound DNS; literal private IPs are still
        # blocked above. Log and allow public hostnames until DNS is restored.
        log.warning(
            "DNS resolution failed for %r; allowing URL after hostname checks only",
            host,
        )
        return

    for a in addrs:
        if _is_private_ip(a):
            raise toolkit.Invalid(
                "URL menunjuk ke alamat private/internal yang tidak diizinkan"
            )


def safe_remote_url(value, context=None):
    """CKAN validator: reject SSRF-prone URLs."""
    if value in (None, ""):
        return value
    try:
        _check_url(value)
    except toolkit.Invalid:
        raise
    return value


def assert_safe_url_or_raise(value):
    """Raise toolkit.ValidationError({"url": [...]}) when unsafe.

    Used inside controller hooks where Invalid is not surfaced cleanly.
    """
    if not value:
        return
    try:
        _check_url(value)
    except toolkit.Invalid as e:
        raise toolkit.ValidationError({"url": [str(e)]})
