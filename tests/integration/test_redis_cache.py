import uuid

from src.cache.redis_client import (
    build_cache_key,
    load_from_cache,
    remove_from_cache,
    save_to_cache
)


def test_a_saved_value_can_be_read_back():
    key = build_cache_key("test", str(uuid.uuid4))
    save_to_cache(key, {"status": "healthy"})

    result = load_from_cache(key)
    assert result == {"status": "healthy"}
    remove_from_cache(key)

def test_reading_a_missing_key_returns_none():
    missing_key = build_cache_key("test", "does-not-exists-" + str(uuid.uuid4))
    result = load_from_cache(missing_key)
    assert result is None

def test_a_removed_value_cannot_be_read_anymore():
    key = build_cache_key("test", str(uuid.uuid4))
    save_to_cache(key, {"status": "stressed"})

    remove_from_cache(key)
    result = load_from_cache(key)
    assert result is None

def test_the_cache_key_is_built_in_a_consistent_format():
    key = build_cache_key("region", "abc1234")
    assert key == "forest:region:abc1234"