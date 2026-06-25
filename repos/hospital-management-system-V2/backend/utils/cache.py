"""
Shared Redis cache utilities.

Provides cache_get, cache_set, and event-based invalidation helpers
used across all blueprints.  All functions handle Redis failures
gracefully — a Redis outage never breaks a request.
"""

import json
import logging
from flask import current_app

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _redis():
    """Return the Redis client attached to the current Flask app."""
    return current_app.redis_client


def _ttl():
    """Return the configured cache TTL in seconds (default 300)."""
    return current_app.config.get("REDIS_CACHE_EXPIRE", 300)


def cache_get(key):
    """Return deserialised cached value, or None on miss / error."""
    try:
        raw = _redis().get(key)
        if raw is not None:
            return json.loads(raw)
    except Exception:
        logger.warning("Redis read failed for key %s, falling back to DB", key)
    return None


def cache_set(key, value, ttl=None):
    """Serialise *value* to JSON and store with TTL. Fails silently."""
    try:
        _redis().setex(key, ttl or _ttl(), json.dumps(value))
    except Exception:
        logger.warning("Redis write failed for key %s", key)


def cache_delete(*keys):
    """Delete one or more exact keys. Fails silently."""
    try:
        _redis().delete(*keys)
    except Exception:
        logger.warning("Redis delete failed for keys %s", keys)


def cache_delete_pattern(pattern):
    """Delete all keys matching a glob *pattern* (e.g. ``patient:doctors:*``).

    Uses SCAN so it never blocks the server on large key-spaces.
    """
    try:
        redis = _redis()
        for key in redis.scan_iter(pattern):
            redis.delete(key)
    except Exception:
        logger.warning("Redis pattern delete failed for %s", pattern)


# ---------------------------------------------------------------------------
# Event-based invalidation
#
# Each "event" maps to the set of cache keys / patterns that must be
# flushed when the corresponding data changes.
# ---------------------------------------------------------------------------

def invalidate_on_doctor_change():
    """A doctor was created / updated / deleted / blacklisted."""
    cache_delete("departments:all")
    cache_delete_pattern("patient:doctors:*")


def invalidate_on_department_change():
    """A department was created / updated / deleted."""
    cache_delete("departments:all")
    cache_delete_pattern("patient:doctors:*")
