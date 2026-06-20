"""Redis JSON cache helpers."""
import json
from typing import Any, Optional

from redis.asyncio import Redis

from config.logging import get_data_logger
from config.settings import settings

logger = get_data_logger()

_client: Optional[Redis] = None


def get_redis_client() -> Optional[Redis]:
    """Return a shared Redis client when REDIS_URL is configured."""
    global _client
    if not settings.redis_url:
        return None
    if _client is None:
        _client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def get_json(key: str) -> Optional[Any]:
    client = get_redis_client()
    if client is None:
        return None
    try:
        raw = await client.get(key)
        return json.loads(raw) if raw else None
    except Exception as exc:
        logger.debug(f"Redis cache read failed for {key}: {exc}")
        return None


async def set_json(key: str, value: Any, ttl_seconds: int) -> None:
    client = get_redis_client()
    if client is None:
        return
    try:
        await client.set(key, json.dumps(value), ex=ttl_seconds)
    except Exception as exc:
        logger.debug(f"Redis cache write failed for {key}: {exc}")


async def health_check() -> dict:
    client = get_redis_client()
    if client is None:
        return {"status": "disabled"}
    try:
        await client.ping()
        return {"status": "healthy"}
    except Exception as exc:
        return {"status": "unhealthy", "error": str(exc)}


async def close_redis_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
