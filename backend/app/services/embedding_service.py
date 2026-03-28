"""EmbeddingService — Voyage AI embedding wrapper."""

import voyageai

from app.core.config import get_settings


class EmbeddingService:
    """Wraps Voyage AI for document and query embeddings.

    Uses asymmetric embedding (different input_type for documents vs queries)
    as recommended by Voyage AI for Q&A retrieval tasks.
    """

    def __init__(self):
        settings = get_settings()
        self.client = voyageai.Client(api_key=settings.VOYAGE_API_KEY)
        self.model = settings.VOYAGE_EMBED_MODEL

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
