import json
import os
from typing import Any
import redis

_redis_connection: redis.Redis | None = None
_DEFAULT_EXPIRY_SECONDS = 3600


def get_cache_connection() -> redis.Redis:
    global _redis_connection
    if _redis_connection is None:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        _redis_connection = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )

    return _redis_connection

def build_cache_key(*parts:str) -> str:
    # Example: build_cache_key("region", "abc123") -> "forest:region:abc123"
    return "forest:" +":".join(str(p) for p in parts)

def save_to_cache(key: str, value:Any, expires_in_seconds: int = _DEFAULT_EXPIRY_SECONDS) -> None:
    get_cache_connection().set(key, json.dumps(value, default=str), ex=expires_in_seconds)

def load_from_cache(key:str) -> Any | None:
    raw_value = get_cache_connection().get(key)
    return json.loads(raw_value) if raw_value is not None else None

def remove_from_cache(key: str) -> None:
    get_cache_connection().delete(key)