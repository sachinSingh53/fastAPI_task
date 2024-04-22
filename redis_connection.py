import aioredis
from fastapi import Depends

class RedisConnection:
    def __init__(self):
        self.redis = None

    async def connect_to_redis(self):
        self.redis = await aioredis.create_redis_pool('redis://localhost:6379')
        return self.redis

    async def close_redis_connection(self):
        self.redis.close()
        await self.redis.wait_closed()

    async def get_connection(self):
        if self.redis is None or self.redis.closed:
            await self.connect_to_redis()
        try:
            yield self.redis
        finally:
            await self.close_redis_connection()
