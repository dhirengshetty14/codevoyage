"""
Realtime progress publish/subscribe helpers backed by Redis Pub/Sub.
"""

from __future__ import annotations

import json
from typing import AsyncIterator, Dict, Any

import redis.asyncio as redis
import structlog

from app.core.config import settings

logger = structlog.get_logger()

PROGRESS_CHANNEL = "codevoyage:analysis:progress"


async def publish_progress_event(event: Dict[str, Any]) -> None:
    """Publish analysis progress event for websocket fanout."""
    client = await redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    try:
        await client.publish(PROGRESS_CHANNEL, json.dumps(event))
    except Exception as exc:
        logger.warning("Failed to publish progress event", error=str(exc))
    finally:
        await client.close()


async def subscribe_progress_events() -> AsyncIterator[Dict[str, Any]]:
    """Yield progress events from redis pubsub channel."""
    client = await redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    pubsub = client.pubsub()
    await pubsub.subscribe(PROGRESS_CHANNEL)
    try:
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            raw = message.get("data")
            if not raw:
                continue
            try:
                yield json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("Invalid progress payload in pubsub", payload=raw)
    finally:
        await pubsub.unsubscribe(PROGRESS_CHANNEL)
        await pubsub.close()
        await client.close()
