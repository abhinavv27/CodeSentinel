from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from app.core.config import get_settings
from app.services.cache_service import CacheService
import asyncio
from functools import lru_cache
import structlog

logger = structlog.get_logger()
settings = get_settings()

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2


@lru_cache
def get_embedder() -> SentenceTransformer:
    """Load and cache the sentence transformer model."""
    return SentenceTransformer("all-MiniLM-L6-v2")


class RagService:
    """Vector store service for codebase context and developer feedback memory."""

    def __init__(self):
        self.client = QdrantClient(url=settings.qdrant_url)
        self.embedder = get_embedder()
        self.cache = CacheService()
        self.collection = settings.qdrant_collection
        self.feedback_collection = settings.qdrant_feedback_collection
        self._ensure_collections()

    def _ensure_collections(self) -> None:
        """Create the Qdrant collections if they don't exist."""
        try:
            existing = {c.name for c in self.client.get_collections().collections}
            # Main codebase collection
            if self.collection not in existing:
                self.client.create_collection(
                    collection_name=self.collection,
                    vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
                )
                logger.info("qdrant_collection_created", collection=self.collection)
            
            # Feedback memory collection
            if self.feedback_collection not in existing:
                self.client.create_collection(
                    collection_name=self.feedback_collection,
                    vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
                )
                logger.info("qdrant_feedback_collection_created", collection=self.feedback_collection)
        except Exception as e:
            logger.warning("qdrant_ensure_collections_failed", error=str(e))

    async def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text, checking cache first."""
        cached = await self.cache.get_embedding(text)
        if cached:
            return cached
        
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(None, self.embedder.encode, text)
        vector = embedding.tolist()
        await self.cache.set_embedding(text, vector)
        return vector

    async def retrieve_context(self, query: str, top_k: int = 5) -> list[str]:
        """Embed the query and retrieve top-k similar code snippets from Qdrant."""
        try:
            vector = await self._get_embedding(query)
            results = self.client.search(
                collection_name=self.collection,
                query_vector=vector,
                limit=top_k,
            )
            return [r.payload.get("content", "") for r in results if r.payload]
        except Exception as e:
            logger.warning("qdrant_retrieve_failed", error=str(e))
            return []

    async def retrieve_feedback_memory(self, query: str, top_k: int = 3) -> list[dict]:
        """Search for historical rejections/false positives similar to the current code."""
        try:
            vector = await self._get_embedding(query)
            results = self.client.search(
                collection_name=self.feedback_collection,
                query_vector=vector,
                limit=top_k,
            )
            return [r.payload for r in results if r.payload]
        except Exception as e:
            logger.warning("qdrant_feedback_retrieve_failed", error=str(e))
            return []

    def index_file(self, file_path: str, content: str, chunk_size: int = 100) -> None:
        """Split a source file into word chunks and upsert embeddings into Qdrant."""
        words = content.split()
        if not words:
            return

        chunks = [
            " ".join(words[i : i + chunk_size])
            for i in range(0, len(words), chunk_size)
        ]
        points = []
        for i, chunk in enumerate(chunks):
            embedding = self.embedder.encode(chunk).tolist()
            point_id = abs(hash(f"{file_path}:{i}")) % (2**31)
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={"file_path": file_path, "content": chunk, "chunk_index": i},
                )
            )

        try:
            self.client.upsert(collection_name=self.collection, points=points)
        except Exception as e:
            logger.error("qdrant_upsert_failed", file=file_path, error=str(e))

    async def index_feedback(self, finding_data: dict, feedback_type: str) -> None:
        """Store identifying characteristics of a rejected/accepted finding to improve future reviews."""
        text_to_embed = f"{finding_data['explanation']} {finding_data['summary']}"
        vector = await self._get_embedding(text_to_embed)
        
        point_id = abs(hash(f"{finding_data['id']}:{feedback_type}")) % (2**31)
        payload = {
            "finding_id": finding_data["id"],
            "type": feedback_type,
            "category": finding_data["category"],
            "explanation": finding_data["explanation"],
            "summary": finding_data["summary"],
            "code_context": finding_data.get("code_context", "")
        }
        
        try:
            self.client.upsert(
                collection_name=self.feedback_collection,
                points=[PointStruct(id=point_id, vector=vector, payload=payload)]
            )
            logger.info("feedback_indexed", finding_id=finding_data["id"], type=feedback_type)
        except Exception as e:
            logger.error("feedback_index_failed", finding_id=finding_data["id"], error=str(e))
