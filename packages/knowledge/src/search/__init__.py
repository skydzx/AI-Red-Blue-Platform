"""Semantic search service for knowledge base."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Any
from pydantic import BaseModel, Field

from ai_red_blue_common import generate_uuid


class SearchResult(BaseModel):
    """Search result with relevance score."""

    id: str = Field(default_factory=generate_uuid)
    document_id: str
    title: str
    excerpt: str
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # Highlight
    highlights: list[str] = Field(default_factory=list)

    # Metadata
    document_type: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    author: Optional[str] = None

    # Timing
    searched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SearchQuery(BaseModel):
    """Search query with filters."""

    query: str
    filters: dict[str, Any] = Field(default_factory=dict)
    document_types: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

    # Pagination
    limit: int = 10
    offset: int = 0

    # Options
    include_highlights: bool = True
    include_metadata: bool = True


class KnowledgeSearchService:
    """Semantic search service for knowledge base."""

    def __init__(self):
        from ai_red_blue_common import get_logger

        self.logger = get_logger("search-service")
        self.index: dict[str, list[float]] = {}  # document_id -> embedding
        self.documents: dict[str, dict] = {}  # document_id -> document data

    async def index_document(
        self,
        document_id: str,
        content: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Index a document for search."""
        # Generate embedding (placeholder)
        embedding = await self._generate_embedding(content)

        self.index[document_id] = embedding
        self.documents[document_id] = {
            "content": content,
            "metadata": metadata or {},
        }
        self.logger.info(f"Indexed document: {document_id}")

    async def _generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text (placeholder)."""
        # In production, use sentence-transformers or similar
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()[:64]
        return [b / 255.0 for b in hash_bytes]

    async def search(
        self,
        query: str,
        filters: Optional[dict[str, Any]] = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Search the knowledge base."""
        query_embedding = await self._generate_embedding(query)

        results = []
        for doc_id, doc_embedding in self.index.items():
            score = self._cosine_similarity(query_embedding, doc_embedding)
            doc = self.documents[doc_id]

            results.append(
                SearchResult(
                    document_id=doc_id,
                    title=doc["metadata"].get("title", "Unknown"),
                    excerpt=doc["content"][:200],
                    relevance_score=score,
                    document_type=doc["metadata"].get("type"),
                    tags=doc["metadata"].get("tags", []),
                )
            )

        # Sort by relevance
        results.sort(key=lambda r: r.relevance_score, reverse=True)

        return results[:limit]

    def _cosine_similarity(
        self,
        vec1: list[float],
        vec2: list[float],
    ) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 * norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    async def delete_index(self, document_id: str) -> bool:
        """Remove a document from the index."""
        if document_id in self.index:
            del self.index[document_id]
            del self.documents[document_id]
            self.logger.info(f"Removed document from index: {document_id}")
            return True
        return False

    def get_statistics(self) -> dict[str, Any]:
        """Get search index statistics."""
        return {
            "indexed_documents": len(self.index),
            "index_size_bytes": sum(
                len(str(v)) for v in self.index.values()
            ),
        }
