"""
Multi-layer caching implementation
Redis (hot) + PostgreSQL (cold) + file cache
"""

import json
import hashlib
from typing import Optional, Any
from functools import wraps
import redis.asyncio as redis
import structlog
from app.core.config import settings

logger = structlog.get_logger()


class CacheManager:
    """Multi-layer cache manager"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        
    async def connect(self):
        """Connect to Redis"""
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("Cache manager connected to Redis")

    async def _ensure_connected(self) -> bool:
        if self.redis_client is not None:
            return True
        try:
            await self.connect()
            return True
        except Exception as e:
            logger.warning("Cache unavailable", error=str(e))
            return False
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Cache manager disconnected from Redis")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{settings.REDIS_CACHE_PREFIX}{prefix}:{key_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not await self._ensure_connected():
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                logger.debug("Cache hit", key=key)
                return json.loads(value)
            logger.debug("Cache miss", key=key)
            return None
        except Exception as e:
            logger.error("Cache get error", error=str(e), key=key)
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = settings.CACHE_TTL_SECONDS
    ):
        """Set value in cache"""
        if not await self._ensure_connected():
            return
        
        try:
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(value)
            )
            logger.debug("Cache set", key=key, ttl=ttl)
        except Exception as e:
            logger.error("Cache set error", error=str(e), key=key)
    
    async def delete(self, key: str):
        """Delete value from cache"""
        if not await self._ensure_connected():
            return
        
        try:
            await self.redis_client.delete(key)
            logger.debug("Cache delete", key=key)
        except Exception as e:
            logger.error("Cache delete error", error=str(e), key=key)
    
    async def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        if not await self._ensure_connected():
            return
        
        try:
            keys = await self.redis_client.keys(f"{settings.REDIS_CACHE_PREFIX}{pattern}*")
            if keys:
                await self.redis_client.delete(*keys)
                logger.info("Cache cleared", pattern=pattern, count=len(keys))
        except Exception as e:
            logger.error("Cache clear error", error=str(e), pattern=pattern)


# Global cache manager instance
cache_manager = CacheManager()


def cached(prefix: str, ttl: int = settings.CACHE_TTL_SECONDS):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache_manager._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = await cache_manager.get(key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache_manager.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator
