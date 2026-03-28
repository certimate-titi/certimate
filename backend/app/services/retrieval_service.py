"""RetrievalService — RAG retrieval using pgvector."""

import uuid

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.repositories.resource_chunk_repository import ResourceChunkRepository
from app.services.embedding_service import EmbeddingService


class RetrievalService:
    """Handles vector search and context assembly for RAG."""

    def __init__(self, db: Session):
        self.chunk_repo = ResourceChunkRepository(db)
        self.embedding_service = EmbeddingService()
        self.settings = get_settings()

    def retrieve(
        self,
        query: str,
        resource_ids: list[uuid.UUID],
        top_k: int | None = None,
    ) -> list[dict]:
        """Embed query and search for similar chunks.

        Args:
            query: The search query text.
            resource_ids: Resource IDs to scope the search (security boundary).
            top_k: Max results to return. Defaults to settings.RETRIEVAL_TOP_K.

        Returns:
            List of dicts with keys: chunk_id, content, distance,
            source_page_start, source_page_end, resource_id, node_id.
        """
        if not resource_ids:
            return []

        if top_k is None:
            top_k = self.settings.RETRIEVAL_TOP_K

        query_embedding = self.embedding_service.embed_query(query)
        results = self.chunk_repo.search_similar(query_embedding, resource_ids, top_k)

        return [
            {
                "chunk_id": str(r["chunk"].id),
                "content": r["chunk"].content,
                "distance": r["distance"],
                "source_page_start": r["chunk"].source_page_start,
                "source_page_end": r["chunk"].source_page_end,
                "resource_id": str(r["chunk"].resource_id),
                "node_id": str(r["chunk"].node_id) if r["chunk"].node_id else None,
                "token_count": r["chunk"].token_count,
            }
            for r in results
        ]

    def build_context_string(
        self,
        retrieved_chunks: list[dict],
        max_tokens: int = 4000,
    ) -> str:
        """Assemble retrieved chunks into a context string for Claude.

        Concatenates chunks in relevance order with page citations,
        stopping when max_tokens is reached.
        """
        parts: list[str] = []
        total_tokens = 0

        for chunk in retrieved_chunks:
            token_count = chunk.get("token_count", 0)
            if total_tokens + token_count > max_tokens and parts:
                break

            page_info = ""
            if chunk.get("source_page_start") is not None:
                if chunk.get("source_page_end") and chunk["source_page_end"] != chunk["source_page_start"]:
                    page_info = f" [p.{chunk['source_page_start']}-{chunk['source_page_end']}]"
                else:
                    page_info = f" [p.{chunk['source_page_start']}]"

            parts.append(f"{chunk['content']}{page_info}")
            total_tokens += token_count

        return "\n\n---\n\n".join(parts)
