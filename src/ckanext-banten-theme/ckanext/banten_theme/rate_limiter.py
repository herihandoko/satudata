"""Login rate limiting + lockout for /user/login (pentest finding HIGH-2).

Strategy
--------
- Apply a Flask `before_app_request` hook to POST /user/login.
- Track 2 counters in Redis (TTL-based, auto-clean):
    bl:login:ip:<ip>           5 per 15 min  → HTTP 429
    bl:login:user:<username>  10 per 1 hour  → HTTP 429 + lockout 30 min
- Lockout (`bl:login:lockout:<username>`) is checked first and short-circuits.
- On a successful login (response 302), counters for the IP + username + lockout
  are cleared so legitimate users with a typo don't accumulate state.
- Failures (200 response = login page re-rendered with error) keep counters.

Fail-open: if Redis is unavailable for any reason, requests pass through
unrestricted. This avoids turning a Redis blip into a site-wide outage; the
rest of the security stack still applies.

Tuning is intentionally simple constants here. Move to env vars if needed.
"""

from __future__ import annotations

import logging
import os

from flask import Blueprint, current_app, make_response, request

try:
    import redis  # type: ignore
except Exception:  # noqa: BLE001
    redis = None  # type: ignore

log = logging.getLogger(__name__)

LOGIN_PATH = "/user/login"

# Limits
IP_WINDOW_SEC = 15 * 60     # 15 minutes
IP_MAX_FAILS = 5
USER_WINDOW_SEC = 60 * 60   # 1 hour
USER_MAX_FAILS = 10
LOCKOUT_SEC = 30 * 60       # 30 minutes

_REDIS_CLIENT = None


def _get_redis():
    """Lazy-init Redis client. Returns None if redis lib unavailable."""
    global _REDIS_CLIENT
    if _REDIS_CLIENT is not None:
        return _REDIS_CLIENT
    if redis is None:
        return None
    url = (
        current_app.config.get("ckan.redis.url")
        or os.environ.get("CKAN_REDIS_URL")
        or "redis://redis:6379/1"
    )
    try:
        _REDIS_CLIENT = redis.from_url(
            url, socket_timeout=2, socket_connect_timeout=2
        )
        _REDIS_CLIENT.ping()
    except Exception as e:  # noqa: BLE001
        log.warning("rate-limit: redis init failed: %s", e)
        _REDIS_CLIENT = None
    return _REDIS_CLIENT


def _client_ip() -> str:
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _too_many(retry_after):
    body = (
        "Terlalu banyak percobaan login. Coba lagi setelah "
        f"{int(retry_after) if retry_after else LOCKOUT_SEC} detik."
    )
    resp = make_response(body, 429)
    resp.headers["Retry-After"] = str(
        int(retry_after) if retry_after and retry_after > 0 else LOCKOUT_SEC
    )
    resp.headers["Content-Type"] = "text/plain; charset=utf-8"
    return resp


def _login_before_request():
    """Block / throttle POST /user/login. Pass other requests through."""
    if request.method != "POST" or request.path != LOGIN_PATH:
        return None

    r = _get_redis()
    if r is None:
        return None  # fail-open

    ip = _client_ip()
    username = (request.form.get("login") or "").strip().lower()

    user_lockout_key = (
        f"bl:login:lockout:{username}" if username else None
    )

    try:
        if user_lockout_key and r.exists(user_lockout_key):
            ttl = r.ttl(user_lockout_key)
            log.warning(
                "rate-limit: locked-out user=%s ip=%s ttl=%s",
                username, ip, ttl,
            )
            return _too_many(ttl)

        ip_key = f"bl:login:ip:{ip}"
        ip_count = r.incr(ip_key)
        if ip_count == 1:
            r.expire(ip_key, IP_WINDOW_SEC)
        if ip_count > IP_MAX_FAILS:
            ttl = r.ttl(ip_key)
            log.warning(
                "rate-limit: ip-exceeded ip=%s count=%s ttl=%s",
                ip, ip_count, ttl,
            )
            return _too_many(ttl)

        if username:
            user_key = f"bl:login:user:{username}"
            user_count = r.incr(user_key)
            if user_count == 1:
                r.expire(user_key, USER_WINDOW_SEC)
            if user_count > USER_MAX_FAILS:
                r.setex(user_lockout_key, LOCKOUT_SEC, "1")
                log.warning(
                    "rate-limit: user-lockout user=%s ip=%s count=%s",
                    username, ip, user_count,
                )
                return _too_many(LOCKOUT_SEC)
    except Exception as e:  # noqa: BLE001
        log.warning("rate-limit: redis op failed, failing open: %s", e)
        return None

    return None


def _login_after_request(response):
    """Reset counters on successful login (CKAN responds 302 on success)."""
    if request.method != "POST" or request.path != LOGIN_PATH:
        return response
    if response.status_code != 302:
        return response

    r = _get_redis()
    if r is None:
        return response

    ip = _client_ip()
    username = (request.form.get("login") or "").strip().lower()
    try:
        r.delete(f"bl:login:ip:{ip}")
        if username:
            r.delete(f"bl:login:user:{username}")
            r.delete(f"bl:login:lockout:{username}")
    except Exception as e:  # noqa: BLE001
        log.debug("rate-limit: reset counters failed: %s", e)
    return response


def get_blueprint() -> Blueprint:
    """Blueprint whose only job is to register app-wide hooks."""
    bp = Blueprint("banten_rate_limit", __name__)
    bp.before_app_request(_login_before_request)
    bp.after_app_request(_login_after_request)
    return bp
