import hashlib
import logging
import pickle
import re
import time
from datetime import timedelta
from pathlib import Path

CACHE_DIR = Path("./.devstash_cache")
_TTL_PATTERN = re.compile(r"(?P<value>\d+)(?P<unit>[smhdw])")

logger = logging.getLogger("devstash")


def parse_ttl(ttl_str: str) -> timedelta:
    match = _TTL_PATTERN.fullmatch(ttl_str.strip())
    if not match:
        raise ValueError(f"Invalid TTL format: {ttl_str}")
    value = int(match.group("value"))
    unit = match.group("unit")
    if unit == "s":
        return timedelta(seconds=value)
    elif unit == "m":
        return timedelta(minutes=value)
    elif unit == "h":
        return timedelta(hours=value)
    elif unit == "d":
        return timedelta(days=value)
    elif unit == "w":
        return timedelta(weeks=value)
    else:
        raise ValueError(f"Unsupported TTL unit: {unit}. Must be one of s, m, h, d, w.")


def _hash_args_kwargs(args, kwargs) -> str:
    """
    Deterministically hash function args/kwargs into a short string.
    Uses pickle for serialization, then SHA256.
    """
    try:
        payload = pickle.dumps((args, kwargs))
        return hashlib.sha256(payload).hexdigest()[:16]  # short digest
    except Exception as e:
        logger.warning(f"[devstash] Could not pickle args/kwargs for cache key: {e}")
        return "nohash"


def devstash_cache_call(func, *args, ttl: str = None, **kwargs):
    """
    Wraps a function call with caching.
    Cache file is named: <module>__<qualname>__<hash>.pkl
    TTL optional: e.g. ttl="1d", "30m", "2h"
    """
    mod = func.__module__ or "main"
    qual = getattr(func, "__qualname__", func.__name__)
    arg_hash = _hash_args_kwargs(args, kwargs)

    filename = f"{mod}__{qual}__{arg_hash}.pkl"
    path = CACHE_DIR / filename.replace("<", "_").replace(">", "_")

    if path.exists():
        if ttl:
            try:
                td = parse_ttl(ttl)
                age = time.time() - path.stat().st_mtime
                if age <= td.total_seconds():
                    with open(path, "rb") as f:
                        logger.debug(f"[devstash] Cache valid, loading from {path}")
                        return pickle.load(f)
                else:
                    logger.debug(f"[devstash] Cache expired (age {age:.0f}s > {ttl}), refreshing...")
            except Exception as e:
                logger.warning(f"[devstash] Failed to apply TTL ({ttl}): {e}")
        else:
            with open(path, "rb") as f:
                logger.debug(f"[devstash] Cache hit, loading from {path}")
                return pickle.load(f)

    # Cache miss or expired
    logger.debug("[devstash] No valid cache available, calling actual...")
    result = func(*args, **kwargs)

    try:
        CACHE_DIR.mkdir(exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(result, f)
            logger.debug(f"[devstash] Saved result to {path}")
    except Exception:
        logger.exception("[devstash] Failed to save object.")

    return result
