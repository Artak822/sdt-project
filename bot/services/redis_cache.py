import json
import logging
from typing import Optional, List

import redis.asyncio as redis

from bot.config import settings

logger = logging.getLogger(__name__)
_client: Optional[redis.Redis] = None


async def get_client() -> redis.Redis:
    global _client
    if not _client:
        _client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


async def close_client() -> None:
    global _client
    if _client:
        await _client.aclose()
        _client = None


async def get_next_profile_user_id(user_id: int) -> Optional[int]:
    client = await get_client()
    value = await client.rpop(f"session:{user_id}:queue")
    return int(value) if value else None


async def push_profile_user_ids(user_id: int, profile_user_ids: List[int]) -> None:
    if not profile_user_ids:
        return
    client = await get_client()
    await client.lpush(f"session:{user_id}:queue", *[str(uid) for uid in profile_user_ids])
    await client.expire(f"session:{user_id}:queue", 1800)


async def cache_profile(profile_user_id: int, profile_data: dict) -> None:
    client = await get_client()
    await client.set(f"profile:{profile_user_id}:data", json.dumps(profile_data), ex=3600)


async def get_cached_profile(profile_user_id: int) -> Optional[dict]:
    client = await get_client()
    data = await client.get(f"profile:{profile_user_id}:data")
    return json.loads(data) if data else None


async def invalidate_profile_cache(profile_user_id: int) -> None:
    client = await get_client()
    await client.delete(f"profile:{profile_user_id}:data")


async def mark_seen(user_id: int, seen_user_id: int) -> None:
    client = await get_client()
    key = f"session:{user_id}:seen"
    await client.sadd(key, str(seen_user_id))
    await client.expire(key, 86400)  # сброс через 24 часа


async def get_seen_ids(user_id: int) -> list[int]:
    client = await get_client()
    members = await client.smembers(f"session:{user_id}:seen")
    return [int(m) for m in members]
