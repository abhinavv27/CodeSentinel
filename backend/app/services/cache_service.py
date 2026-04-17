import redis.asyncio as redis
import json
import hashlib
from typing import Any, Optional
from app.core.config import get_settings
import structlog

logger = structlog.get_logger()
settings = get_settings()

class CacheService:
    """Service for caching LLM results and RAG embeddings to reduce latency and costs."""

    def __init__(self):
        self.client = redis.from_url(settings.redis_url, decode_responses=True)

    @staticmethod
    def _generate_key(content: str, salt: str = "") -> str:
        """Generate a deterministic hash key for the given content."""
        return hashlib.sha256(f"{salt}:{content}".encode()).hexdigest()

    async def get_finding(self, diff_chunk: str) -> Optional[list[dict]]:
        """Retrieve cached findings for a specific diff chunk."""
        key = f"finding:{self._generate_key(diff_chunk)}"
        try:
            data = await self.client.get(key)
            if data:
                logger.debug("cache_hit", type="finding", key=key)
                return json.loads(data)
        except Exception as e:
            logger.warning("cache_get_failed", error=str(e))
        return None

    async def set_finding(self, diff_chunk: str, findings: list[dict], ttl: int = 86400) -> None:
        """Cache findings for a diff chunk with a default TTL of 24 hours."""
        key = f"finding:{self._generate_key(diff_chunk)}"
        try:
            await self.client.set(key, json.dumps(findings), ex=ttl)
            logger.debug("cache_set", type="finding", key=key)
        except Exception as e:
            logger.warning("cache_set_failed", error=str(e))

    async def get_embedding(self, text: str) -> Optional[list[float]]:
        """Retrieve cached embedding for a text snippet."""
        key = f"embed:{self._generate_key(text)}"
        try:
            data = await self.client.get(key)
            if data:
                logger.debug("cache_hit", type="embedding", key=key)
                return json.loads(data)
        except Exception as e:
            logger.warning("cache_get_failed", type="embedding", error=str(e))
        return None

    async def set_embedding(self, text: str, vector: list[float], ttl: int = 604800) -> None:
        """Cache embedding for a text snippet with a default TTL of 7 days."""
        key = f"embed:{self._generate_key(text)}"
        try:
            await self.client.set(key, json.dumps(vector), ex=ttl)
            logger.debug("cache_set", type="embedding", key=key)
        except Exception as e:
            logger.warning("cache_set_failed", type="embedding", error=str(e))
