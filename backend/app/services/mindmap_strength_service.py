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

        Algorithm:
        1. Direct binding: count chunks where node_id = this node (already mapped)
        2. Semantic binding: embed node name + count chunks within similarity threshold
        3. Combine: direct count weighted higher, saturate at _STRENGTH_SATURATION_AT
        """
        if not resource_ids:
            return 0.0

        # Layer 1: direct chunk binding (exclude soft-deleted)
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

        # Layer 2: semantic similarity via pgvector
        #   Embed the node name once and query.
        try:
            semantic_count = self._count_similar_chunks(node_name, resource_ids)
        except Exception as exc:  # noqa: BLE001
            # If embedding service fails (e.g. Voyage quota), fall back to direct count only
            logger.warning(
                "strength: semantic search failed for node %s: %s", node_id, exc
            )
            semantic_count = 0

        # Combine: direct weighted 2x
        weighted_total = direct_count * 2 + semantic_count
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
