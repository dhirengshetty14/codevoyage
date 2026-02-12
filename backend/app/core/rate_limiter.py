"""
Rate limiting configuration using token bucket algorithm
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings


# Create rate limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    storage_uri=settings.REDIS_URL,
)
