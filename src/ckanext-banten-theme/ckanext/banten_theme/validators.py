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


def _is_private_ip(addr_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(addr_str)
    except ValueError:
        return False
    nets = _PRIVATE_NETS_V6 if ip.version == 6 else _PRIVATE_NETS_V4
    return any(ip in net for net in nets)


def _resolve_all(host: str):
    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, socket.herror, UnicodeError):
        return None
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

    addrs = _resolve_all(host)
    if addrs is None:
        raise toolkit.Invalid("Host URL tidak dapat di-resolve")

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
