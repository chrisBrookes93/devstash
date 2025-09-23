import hashlib
import logging
import os
import pickle
import re
import time
from datetime import timedelta
from pathlib import Path

_TTL_PATTERN = re.compile(r"(?P<value>\d+)(?P<unit>[smhdw])")

logger = logging.getLogger("devstash")

MAX_FILENAME_LENGTH = 200  # safe limit < 255
CACHE_DIR = Path(os.environ.get("DEVSTASH_CACHE_DIR", "./.devstash_cache"))
RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}


def sanitize_filename(name: str) -> str:
    """
    Sanitize filename against unsafe characters and reserved names.
    """
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
    if safe.split(".")[0].upper() in RESERVED_NAMES:
        safe = "_" + safe
    return safe


def safe_filename(name: str) -> str:
    """
    Ensure filename is safe and <= MAX_FILENAME_LENGTH.
    """
    safe = sanitize_filename(name)
    if len(safe) <= MAX_FILENAME_LENGTH:
        return safe

    base, dot, ext = safe.partition(".")
    h = hashlib.sha256(safe.encode()).hexdigest()[:16]
    trunc = base[: MAX_FILENAME_LENGTH - len(h) - len(ext) - 2]
    return f"{trunc}_{h}{dot}{ext}"


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

    base_name = f"{mod}__{qual}__{arg_hash}.pkl"
    filename = safe_filename(base_name)
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
