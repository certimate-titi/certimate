"""MindmapStrengthService — compute user-data support strength per knowledge node.

Mindmap architecture upgrade §3 — 骨架失焦處理 Strategy E (置信度標示).

Strategy:
- Each knowledge_node has `support_strength` (0.0-1.0).
- Strength = how well the user's resources cover this node's topic.
- Calculation uses vector similarity between node name and user chunks
  embeddings, count of relevant chunks, and per-resource distribution.
- Cached in DB (not recomputed per read).
- Recomputed on:
  - Resource upload finish
  - Resource deletion
  - Unified extraction run

Frontend uses strength to render:
- 0.0            → gray "待補充" badge
- 0.0 < s < 0.3  → dim color + "資料稀疏" warning
- 0.3 ≤ s < 0.7  → normal color + "建議補充更多相關資料"
- s ≥ 0.7        → full color + ready for practice
"""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal
from typing import Iterable

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# Strength calculation tuning (env-var overridable later if needed)
_SIMILARITY_THRESHOLD = 0.60        # cosine similarity cutoff for a chunk to count
_STRENGTH_SATURATION_AT = 5         # 5+ relevant chunks = 1.0 strength
_QUESTION_SATURATION_AT = 10        # 10+ mapped historical questions = 1.0 strength
                                    # (Layer 3 — Feature 34 补強: preseed-mindmaps 場景)


class MindmapStrengthService:
    """Compute and persist `support_strength` for knowledge nodes."""

    def __init__(self, db: Session):
        self.db = db
        self._embed_cache: dict[str, list[float]] | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def recompute_for_subject(self, subject_id: uuid.UUID) -> int:
        """Recompute support_strength for every node in this subject.

        Returns the number of nodes updated.
        """
        nodes = self.db.execute(
            text(
                """
                SELECT id, name, parent_id
                FROM knowledge_nodes
                WHERE subject_id = :sid
                """
            ),
            {"sid": subject_id},
        ).fetchall()

        if not nodes:
            return 0

        # Find all resources for this subject
        resource_ids = [
            r[0]
            for r in self.db.execute(
                text("SELECT id FROM resources WHERE subject_id = :sid"),
                {"sid": subject_id},
            ).fetchall()
        ]

        updated = 0
        for row in nodes:
            node_id, name, _ = row
            strength = self._compute_node_strength(node_id, name, resource_ids)
            self.db.execute(
                text(
                    """
                    UPDATE knowledge_nodes
                    SET support_strength = :s
                    WHERE id = :nid
                    """
                ),
                {"s": float(strength), "nid": node_id},
            )
            updated += 1
        self.db.commit()
        logger.info(
            "[strength] recomputed %d nodes for subject %s", updated, subject_id
        )
        return updated

    def recompute_for_node(self, node_id: uuid.UUID) -> float:
        """Recompute and persist strength for a single node. Returns new strength."""
        row = self.db.execute(
            text(
                """
                SELECT kn.id, kn.name, kn.subject_id
                FROM knowledge_nodes kn
                WHERE kn.id = :nid
                """
            ),
            {"nid": node_id},
        ).first()
        if not row:
            return 0.0
        nid, name, subject_id = row
        resource_ids = [
            r[0]
            for r in self.db.execute(
                text("SELECT id FROM resources WHERE subject_id = :sid"),
                {"sid": subject_id},
            ).fetchall()
        ]
        strength = self._compute_node_strength(nid, name, resource_ids)
        self.db.execute(
            text(
                """
                UPDATE knowledge_nodes
                SET support_strength = :s
                WHERE id = :nid
                """
            ),
            {"s": float(strength), "nid": nid},
        )
        self.db.commit()
        return float(strength)

    # ------------------------------------------------------------------
    # Strength computation
    # ------------------------------------------------------------------

    def _compute_node_strength(
        self,
        node_id: uuid.UUID,
        node_name: str,
        resource_ids: list,
    ) -> float:
        """Compute 0.0-1.0 support strength for a node.

        Algorithm (Feature 34 §3 Strategy E + 考古題補強):
        1. Direct binding: chunks where node_id = this node (user resources)
        2. Semantic binding: pgvector similarity within this subject's chunks
        3. Question binding (NEW): mapped historical questions (questions.node_id)
        4. Combine: direct×2 + semantic×1 + question×1, saturate at 2×5 = 10

        Key fix: previously returned 0.0 when resource_ids was empty, which made
        pure-historical-qa subjects look like empty shells even though they had
        hundreds of mapped questions. Layer 3 gives those subjects real strength.
        """
        # Layer 1: direct chunk binding (exclude soft-deleted)
        direct_count = 0
        if resource_ids:
            direct_count = self.db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM resource_chunks
                    WHERE node_id = :nid
                      AND is_deleted = false
                    """
                ),
                {"nid": node_id},
            ).scalar() or 0

        if direct_count >= _STRENGTH_SATURATION_AT:
            return 1.0

        # Layer 2: semantic similarity via pgvector (only if user has resources)
        semantic_count = 0
        if resource_ids:
            try:
                semantic_count = self._count_similar_chunks(node_name, resource_ids)
            except Exception as exc:  # noqa: BLE001
                # If embedding service fails (e.g. Voyage quota), fall back gracefully
                logger.warning(
                    "strength: semantic search failed for node %s: %s", node_id, exc
                )
                semantic_count = 0

        # Layer 3: historical question binding (NEW — Feature 34 补強)
        # Count questions that have been mapped to this node via
        # UnifiedKnowledgeExtractionService._map_questions_to_nodes().
        # This lets pure-考古題 subjects accumulate non-zero strength.
        question_count = self.db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM questions
                WHERE node_id = :nid
                  AND historical_exam_id IS NOT NULL
                """
            ),
            {"nid": node_id},
        ).scalar() or 0

        # Early saturation on question count alone (10+ questions = full coverage)
        if question_count >= _QUESTION_SATURATION_AT:
            return 1.0

        # Combine: direct×2, semantic×1, question×1
        # Max weighted = 5*2 + X + 10 = can exceed 10, so clamp to 1.0
        weighted_total = direct_count * 2 + semantic_count + question_count
        strength = min(weighted_total / (_STRENGTH_SATURATION_AT * 2), 1.0)
        return round(strength, 3)

    def _count_similar_chunks(
        self, query_text: str, resource_ids: list
    ) -> int:
        """Count chunks with cosine similarity ≥ _SIMILARITY_THRESHOLD to query_text."""
        if not query_text or not resource_ids:
            return 0

        # Lazy import to avoid circular dependency
        from app.services.embedding_service import EmbeddingService

        embedding = EmbeddingService().embed_query(query_text)
        # cosine_distance = 1 - similarity, so threshold the other way
        max_distance = 1.0 - _SIMILARITY_THRESHOLD

        count = self.db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM resource_chunks
                WHERE resource_id = ANY(:rids)
                  AND embedding IS NOT NULL
                  AND is_deleted = false
                  AND (embedding <=> cast(:qvec as vector)) <= :max_dist
                """
            ),
            {
                "rids": resource_ids,
                "qvec": str(embedding),
                "max_dist": max_distance,
            },
        ).scalar() or 0
        return int(count)

    # ------------------------------------------------------------------
    # Display helpers (used by knowledge_nav_service later)
    # ------------------------------------------------------------------

    @staticmethod
    def strength_to_display(strength: float | None) -> dict:
        """Map numeric strength → frontend display hint.

        Returns {"tier": str, "color": str, "label": str, "needs_supplement": bool}
        """
        if strength is None or strength <= 0:
            return {
                "tier": "empty",
                "color": "gray",
                "label": "待補充",
                "needs_supplement": True,
            }
        if strength < 0.3:
            return {
                "tier": "sparse",
                "color": "dim",
                "label": "資料稀疏",
                "needs_supplement": True,
            }
        if strength < 0.7:
            return {
                "tier": "partial",
                "color": "normal",
                "label": "可補充更多資料",
                "needs_supplement": False,
            }
        return {
            "tier": "full",
            "color": "normal",
            "label": "資料充足",
            "needs_supplement": False,
        }
