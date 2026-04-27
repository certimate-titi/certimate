"""RetrievalService — RAG retrieval using pgvector + optional Voyage reranker."""

import logging
import os
import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.repositories.resource_chunk_repository import ResourceChunkRepository
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class RetrievalService:
    """Handles vector search and context assembly for RAG.

    Tier 1-B (2026 architecture upgrade): Two-stage retrieval.
    - Stage 1: pgvector cosine similarity → top 100 (recall)
    - Stage 2: Voyage rerank-2.5 → top_k (precision)
    Gracefully degrades to single-stage if reranker is disabled or fails.
    """

    def __init__(self, db: Session):
        """初始化實例。"""
        self.db = db
        self.chunk_repo = ResourceChunkRepository(db)
        self.embedding_service = EmbeddingService()
        self.settings = get_settings()
        # Rerank config (env-var controlled for safe rollout)
        self.rerank_enabled = (
            os.environ.get("RETRIEVAL_RERANK_ENABLED", "true").lower() == "true"
        )
        self.rerank_candidate_pool = int(
            os.environ.get("RETRIEVAL_RERANK_POOL", "100")
        )

    def retrieve(
        self,
        query: str,
        resource_ids: list[uuid.UUID],
        top_k: int | None = None,
        *,
        user_id: uuid.UUID | str | None = None,
        exclude_mastered: bool = True,
    ) -> list[dict]:
        """Embed query and search for similar chunks.

        Args:
            query: The search query text.
            resource_ids: Resource IDs to scope the search (security boundary).
            top_k: Max results to return. Defaults to settings.RETRIEVAL_TOP_K.
            user_id: Optional user UUID; when provided enables mastery-aware
                     filtering (Tier 1 — Mastery-aware Retrieval).
            exclude_mastered: When True + user_id given, skip chunks whose
                              knowledge_node is already MASTERED. Default True
                              to focus study on weak areas.

        Returns:
            List of dicts with keys: chunk_id, content, distance,
            source_page_start, source_page_end, resource_id, node_id.
        """
        if not resource_ids:
            return []

        if top_k is None:
            top_k = self.settings.RETRIEVAL_TOP_K

        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                user_id = None

        query_embedding = self.embedding_service.embed_query(query)

        # Stage 1: pgvector recall — pull a larger candidate pool when rerank enabled
        stage1_k = (
            max(self.rerank_candidate_pool, top_k)
            if self.rerank_enabled
            else top_k
        )
        candidates = self.chunk_repo.search_similar(
            query_embedding,
            resource_ids,
            stage1_k,
            user_id=user_id,
            exclude_mastered=exclude_mastered,
        )

        # Stage 2: Voyage reranker — precision filter
        if self.rerank_enabled and len(candidates) > top_k:
            try:
                results = self._apply_rerank(query, candidates, top_k, user_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Reranker failed, falling back to pgvector-only results: %s", exc
                )
                results = candidates[:top_k]
        else:
            results = candidates[:top_k]

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

    def _apply_rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int,
        user_id: uuid.UUID | None,
    ) -> list[dict]:
        """Apply Voyage rerank to narrow candidates to top_k.

        Also:
        - Checks Voyage quota (Feature 33 integration) before calling API
        - Records usage to ai_usage_ledger via track_ai_usage
        - Preserves the original pgvector distance in the returned dicts
        """
        from app.middleware.ai_usage_tracker import (
            estimate_voyage_cost,
            track_ai_usage,
        )
        from app.services.voyage_quota_service import (
            VoyageQuotaDegraded,
            VoyageQuotaExceeded,
            VoyageQuotaService,
        )

        documents = [c["chunk"].content for c in candidates]

        # Rough token estimate: query + all docs (~4 chars/token)
        total_chars = len(query) + sum(len(d) for d in documents)
        est_tokens = max(total_chars // 4, 1)
        est_cost = estimate_voyage_cost(est_tokens)

        # Feature 33 — quota gate: if Voyage is degraded/exhausted, skip rerank
        try:
            quota_svc = VoyageQuotaService(self.db)
            quota_svc.check_and_reserve(est_cost)
        except (VoyageQuotaDegraded, VoyageQuotaExceeded) as exc:
            logger.info(
                "Voyage rerank skipped due to quota (%s); falling back to pgvector ranking",
                type(exc).__name__,
            )
            return candidates[:top_k]

        # Call rerank + record usage
        with track_ai_usage(
            self.db, provider="voyage", feature="rerank", user_id=user_id
        ) as tracker:
            rerank_results = self.embedding_service.rerank(
                query=query, documents=documents, top_k=top_k
            )
            tracker.input_tokens = est_tokens
            tracker.cost_usd = est_cost
            tracker.endpoint = f"voyage/rerank/{self.embedding_service.rerank_model}"

        # Remap reranker output back to original chunk dicts
        reordered: list[dict] = []
        for r in rerank_results:
            original = candidates[r["index"]]
            enriched = dict(original)
            enriched["rerank_score"] = r["relevance_score"]
            reordered.append(enriched)
        return reordered

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
