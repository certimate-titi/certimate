"""EmbeddingService — Voyage AI embedding wrapper (+ reranker)."""

import os

from app.core.config import get_settings


class EmbeddingService:
    """Wraps Voyage AI for document and query embeddings + reranking.

    Uses asymmetric embedding (different input_type for documents vs queries)
    as recommended by Voyage AI for Q&A retrieval tasks.

    Also wraps the Voyage rerank-2/rerank-2.5 API for two-stage retrieval
    (Tier 1-B — 2026 architecture upgrade).
    """

    def __init__(self):
        import voyageai
        settings = get_settings()
        self.client = voyageai.Client(api_key=settings.VOYAGE_API_KEY)
        self.model = settings.VOYAGE_EMBED_MODEL
        self.rerank_model = os.environ.get("VOYAGE_RERANK_MODEL", "rerank-2.5")

    def embed_texts(
        self, texts: list[str], input_type: str = "document"
    ) -> list[list[float]]:
        """Batch embed texts for indexing.

        Args:
            texts: List of text strings to embed.
            input_type: "document" for indexing, "query" for retrieval.

        Returns:
            List of embedding vectors (each is list[float] of length 1024).
        """
        if not texts:
            return []

        # Voyage AI supports up to 128 texts per call
        all_embeddings: list[list[float]] = []
        batch_size = 64

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            result = self.client.embed(
                batch,
                model=self.model,
                input_type=input_type,
            )
            all_embeddings.extend(result.embeddings)

        return all_embeddings

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query for retrieval (uses input_type="query")."""
        result = self.client.embed(
            [query],
            model=self.model,
            input_type="query",
        )
        return result.embeddings[0]

    def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 5,
    ) -> list[dict]:
        """Rerank documents by relevance to query using Voyage rerank-2.5.

        Args:
            query: Original search query.
            documents: Raw document content strings to rerank.
            top_k: How many top results to return.

        Returns:
            List of {"index": int, "relevance_score": float} sorted by score desc.
            `index` refers to position in the original documents list.

        Raises:
            Propagates voyageai exceptions; caller should catch and fallback.
        """
        if not documents:
            return []
        result = self.client.rerank(
            query=query,
            documents=documents,
            model=self.rerank_model,
            top_k=top_k,
        )
        return [
            {"index": r.index, "relevance_score": r.relevance_score}
            for r in result.results
        ]
