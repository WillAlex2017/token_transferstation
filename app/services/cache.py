from redis.asyncio import Redis


async def get_cached_response(redis: Redis, key: str) -> str | None:
    return await redis.get(f"cache:{key}")


async def set_cached_response(redis: Redis, key: str, value: str, ttl: int = 300):
    await redis.setex(f"cache:{key}", ttl, value)
