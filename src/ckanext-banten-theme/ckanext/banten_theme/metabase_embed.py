"""Metabase signed embed URL builder for /metrix iframe."""

from __future__ import annotations

import logging
import os
import time

import jwt

log = logging.getLogger(__name__)

# Fallback when METABASE_EMBED_SECRET is not set (local dev / transitional deploy).
_DEFAULT_PUBLIC_PATH = (
    "/metrix-dashboard/public/dashboard/"
    "074806cf-11d0-481b-8714-c78d9856621d"
)


def build_metrix_dashboard_url() -> str:
    """Return iframe src for Metrix.

    Priority:
    1. METABASE_DIRECT_DASHBOARD_URL — full URL (e.g. internal Metabase public link)
    2. Signed JWT embed when METABASE_EMBED_SECRET is set
    3. Public dashboard path fallback (same-origin proxy)
    """
    direct = (os.environ.get("METABASE_DIRECT_DASHBOARD_URL") or "").strip()
    if direct:
        log.debug("Metrix using METABASE_DIRECT_DASHBOARD_URL")
        return direct

    secret = (os.environ.get("METABASE_EMBED_SECRET") or "").strip()
    if not secret:
        path = (
            os.environ.get("METABASE_PUBLIC_DASHBOARD_PATH") or _DEFAULT_PUBLIC_PATH
        ).strip()
        log.warning(
            "METABASE_EMBED_SECRET not set; using public dashboard path %s", path
        )
        return path

    site_url = (
        os.environ.get("METABASE_EMBED_SITE_URL") or "/metrix-dashboard"
    ).strip().rstrip("/")

    try:
        dashboard_id = int(os.environ.get("METABASE_DASHBOARD_ID", "23"))
    except ValueError:
        dashboard_id = 23

    try:
        expiry_minutes = int(os.environ.get("METABASE_EMBED_EXPIRY_MINUTES", "10"))
    except ValueError:
        expiry_minutes = 10

    fragment = (os.environ.get("METABASE_EMBED_FRAGMENT") or "bordered=true&titled=true").strip()
    params = _embed_params()

    payload = {
        "resource": {"dashboard": dashboard_id},
        "params": params,
        "exp": int(time.time()) + (expiry_minutes * 60),
    }

    token = jwt.encode(payload, secret, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8")

    url = f"{site_url}/embed/dashboard/{token}"
    if fragment:
        url = f"{url}#{fragment.lstrip('#')}"
    return url


def _embed_params() -> dict:
    """Optional locked params JSON in METABASE_EMBED_PARAMS, e.g. {"region":"banten"}."""
    raw = (os.environ.get("METABASE_EMBED_PARAMS") or "").strip()
    if not raw:
        return {}
    try:
        import json

        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        log.warning("Invalid METABASE_EMBED_PARAMS: %s", exc)
        return {}
