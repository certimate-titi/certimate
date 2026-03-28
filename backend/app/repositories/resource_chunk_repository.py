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

    def delete_by_resource_id(self, resource_id: uuid.UUID) -> int:
        """Delete all chunks for a resource (for reprocessing). Returns count deleted."""
        stmt = (
            delete(ResourceChunk)
            .where(ResourceChunk.resource_id == resource_id)
        )
        result = self.session.execute(stmt)
        self.session.flush()
        return result.rowcount

    def search_similar(
        self,
        query_embedding: list[float],
        resource_ids: list[uuid.UUID],
        top_k: int = 10,
    ) -> list[dict]:
        """Vector similarity search using pgvector cosine distance.

        Security: scoped to resource_ids so users can only search their own docs.
        Returns list of {"chunk": ResourceChunk, "distance": float}.
        """
        if not resource_ids:
            return []

        stmt = (
            select(
                ResourceChunk,
                ResourceChunk.embedding.cosine_distance(query_embedding).label("distance"),
            )
            .where(ResourceChunk.resource_id.in_(resource_ids))
            .where(ResourceChunk.embedding.isnot(None))
            .order_by("distance")
            .limit(top_k)
        )
        rows = self.session.execute(stmt).all()
        return [{"chunk": row[0], "distance": row[1]} for row in rows]
