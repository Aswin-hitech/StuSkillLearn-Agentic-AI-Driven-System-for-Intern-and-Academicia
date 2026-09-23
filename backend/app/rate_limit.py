from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timezone
from threading import Lock

from fastapi import HTTPException, Request

from app.config import settings

_local_attempts: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def _key(request: Request, identity: str) -> str:
    ip = request.client.host if request.client else "unknown"
    return f"auth:{ip}:{identity.strip().lower()}"


def enforce_login_rate_limit(request: Request, identity: str) -> None:
    key = _key(request, identity)
    try:
        from redis import Redis

        client = Redis.from_url(settings.redis_url, socket_connect_timeout=0.25, socket_timeout=0.25, decode_responses=True)
        value = client.incr(key)
        if value == 1:
            client.expire(key, settings.login_rate_limit_window_seconds)
        if value > settings.login_rate_limit_attempts:
            ttl = max(1, client.ttl(key))
            raise HTTPException(status_code=429, detail=f"Too many login attempts. Try again in {ttl} seconds")
        return
    except HTTPException:
        raise
    except Exception:
        if settings.is_production:
            raise HTTPException(status_code=503, detail="Authentication protection service unavailable")

    # Development fallback only. Production fails closed when Redis is unavailable.
    now = datetime.now(timezone.utc).timestamp()
    cutoff = now - settings.login_rate_limit_window_seconds
    with _lock:
        queue = _local_attempts[key]
        while queue and queue[0] < cutoff:
            queue.popleft()
        if len(queue) >= settings.login_rate_limit_attempts:
            raise HTTPException(status_code=429, detail="Too many login attempts. Try again later")
        queue.append(now)

def clear_login_rate_limit(request: Request, identity: str) -> None:
    """Clear the failed-attempt bucket after a successful authentication.

    Verification/reset request throttles intentionally do not call this helper;
    they are request-rate limits rather than failed-login counters.
    """
    key = _key(request, identity)
    try:
        from redis import Redis

        client = Redis.from_url(settings.redis_url, socket_connect_timeout=0.25, socket_timeout=0.25, decode_responses=True)
        client.delete(key)
        return
    except Exception:
        if settings.is_production:
            # Authentication already succeeded. Do not turn a post-auth cleanup
            # outage into a login failure; the next protected endpoint/readiness
            # check will still fail closed if Redis is unavailable in production.
            return

    with _lock:
        _local_attempts.pop(key, None)

