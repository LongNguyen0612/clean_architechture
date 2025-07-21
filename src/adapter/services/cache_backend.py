from src.app.services import CacheBackend
import redis.asyncio as redis_async
from redis import exceptions
import logging
import asyncio

logger = logging.getLogger(__name__)


class RetryingRedis(redis_async.Redis):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._retry_count = 0
        self._max_retries = 3
        self._logger = logger

    async def execute_command(self, *args, **options):
        self._retry_count = 0
        while True:
            try:
                return await super().execute_command(*args, **options)
            except (
                    exceptions.ConnectionError,
                    exceptions.TimeoutError,
                    exceptions.RedisError,
            ) as e:
                self._retry_count += 1
                if self._retry_count > self._max_retries:
                    logger.exception("Redis connection timeout")
                    return False
                backoff = 2 ** (self._retry_count - 1)
                self._logger.warning(
                    f"Redis operation failed. Retry attempt {self._retry_count}/{self._max_retries} "
                    f"with {self._max_retries - self._retry_count} retries remaining. "
                    f"Next retry in {backoff} seconds. Error: {str(e)}"
                )
                await asyncio.sleep(backoff)


class RedisCacheBackend(CacheBackend):
    def __init__(self, redis_url: str):
        self.redis_client = RetryingRedis.from_url(
            redis_url,
            socket_timeout=5.0,
            socket_connect_timeout=2.0,
            socket_keepalive=True,
            health_check_interval=30,
            retry_on_timeout=True,
        )

    async def get(self, key: str) -> bytes:
        """Get value from Redis"""
        return await self.redis_client.get(key)

    async def set(self, key: str, data: bytes, expire: int = None) -> None:
        """Set value in Redis with optional expiration"""
        if expire:
            await self.redis_client.setex(key, expire, data)
        else:
            await self.redis_client.set(key, data)

    async def delete(self, key: str) -> None:
        """Delete value from Redis"""
        await self.redis_client.delete(key)
