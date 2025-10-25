import redis.asyncio as redis
from typing import Optional
import os


class RedisClient:
    """
    Async Redis client wrapper with basic key-value operations.
    """
    
    def __init__(self):
        """Initialize Redis connection."""
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True  # Automatically decode responses to strings
        )
    
    async def set_value(self, key: str, value: str, expiry: Optional[int] = None) -> bool:
        """
        Set a key-value pair in Redis.
        """
        if expiry:
            return await self.client.setex(key, expiry, value)
        else:
            return await self.client.set(key, value)
    
    async def get_value(self, key: str) -> Optional[str]:
        """
        Get a value from Redis by key or None.
        """
        return await self.client.get(key)
    
    async def ping(self) -> bool:
        """
        Ping Redis to check connection.
        """
        return await self.client.ping()
    
    async def close(self):
        """Close the Redis connection."""
        await self.client.close()


# Global Redis client instance
redis_client = RedisClient()
