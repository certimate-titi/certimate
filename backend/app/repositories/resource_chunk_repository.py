"""ResourceChunk Repository — SQLAlchemy + pgvector implementation."""

import uuid
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.resource_chunk import ResourceChunk


class ResourceChunkRepository:

    def __init__(self, session: Session):
        self.session = session

    def save_batch(self, chunks: list[ResourceChunk]) -> list[ResourceChunk]:
        """Bulk insert chunks. Caller controls commit."""
        self.session.add_all(chunks)
        self.session.flush()
        return chunks

    def find_by_resource_id(self, resource_id: uuid.UUID) -> list[ResourceChunk]:
        """Get all chunks for a resource, ordered by chunk_index."""
        stmt = (
            select(ResourceChunk)
            .where(ResourceChunk.resource_id == resource_id)
            .order_by(ResourceChunk.chunk_index)
        )
        return list(self.session.execute(stmt).scalars().all())

    def delete_by_resource_id(
        self, resource_id: uuid.UUID, hard: bool = False
    ) -> int:
        """Soft-delete chunks by default (T2-A).

        hard=True triggers legacy hard delete for reprocessing scenarios where
        we need to re-embed and replace rows entirely.
        """
        if hard:
            stmt = (
                delete(ResourceChunk)
                .where(ResourceChunk.resource_id == resource_id)
            )
            result = self.session.execute(stmt)
            self.session.flush()
            return result.rowcount

        # Soft delete
        from sqlalchemy import update
        from datetime import datetime, timezone
        stmt = (
            update(ResourceChunk)
            .where(ResourceChunk.resource_id == resource_id)
            .where(ResourceChunk.is_deleted.is_(False))
            .values(is_deleted=True, deleted_at=datetime.now(timezone.utc))
        )
        result = self.session.execute(stmt)
        self.session.flush()
        return result.rowcount

    def search_similar(
        self,
        query_embedding: list[float],
        resource_ids: list[uuid.UUID],
        top_k: int = 10,
        *,
        user_id: uuid.UUID | None = None,
        exclude_mastered: bool = True,
    ) -> list[dict]:
        """Vector similarity search using pgvector cosine distance.

        Security: scoped to resource_ids so users can only search their own docs.

        Tier 1 (Mastery-aware): when user_id is provided and exclude_mastered=True,
        this joins node_mastery and filters out chunks whose knowledge_node is already
        MASTERED by the user. Chunks without an associated node_mastery row (unseen
        content or new users) are kept — fallback is safe for cold-start.

        Returns list of {"chunk": ResourceChunk, "distance": float}.
        """
        if not resource_ids:
            return []

        from sqlalchemy import or_
        from app.models.node_mastery import NodeMastery

        stmt = select(
            ResourceChunk,
            ResourceChunk.embedding.cosine_distance(query_embedding).label("distance"),
        )

        if user_id is not None and exclude_mastered:
            # LEFT JOIN: chunks without mastery row (nm.status IS NULL) are kept
            stmt = stmt.outerjoin(
                NodeMastery,
                (NodeMastery.node_id == ResourceChunk.node_id)
                & (NodeMastery.user_id == user_id),
            ).where(
                or_(NodeMastery.status.is_(None), NodeMastery.status != "MASTERED")
            )

        stmt = (
            stmt.where(ResourceChunk.resource_id.in_(resource_ids))
            .where(ResourceChunk.embedding.isnot(None))
            .where(ResourceChunk.is_deleted.is_(False))  # T2-A 軟刪過濾
            .order_by("distance")
            .limit(top_k)
        )
        rows = self.session.execute(stmt).all()
        return [{"chunk": row[0], "distance": row[1]} for row in rows]
