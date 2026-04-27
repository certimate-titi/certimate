"""ResourceChunk Repository — SQLAlchemy + pgvector implementation."""

import uuid
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.resource_chunk import ResourceChunk


class ResourceChunkRepository:
    """資源切片資料存取 Repository（pgvector 向量檢索）。

    封裝 ResourceChunk ORM 的批次寫入、查詢、軟/硬刪除與向量相似度檢索，
    供 RAG service 使用。
    """

    def __init__(self, session: Session):
        """初始化 Repository。

        Args:
            session: SQLAlchemy Session。
        """
        self.session = session

    def save_batch(self, chunks: list[ResourceChunk]) -> list[ResourceChunk]:
        """批次寫入 chunks（呼叫端自行控制 commit）。

        Args:
            chunks: 待寫入的 ResourceChunk list。

        Returns:
            已 flush 的 ResourceChunk list。
        """
        self.session.add_all(chunks)
        self.session.flush()
        return chunks

    def find_by_resource_id(self, resource_id: uuid.UUID) -> list[ResourceChunk]:
        """查詢資源的所有 chunks，依 ``chunk_index`` 升冪排序。

        Args:
            resource_id: Resource UUID。

        Returns:
            list of ResourceChunk。
        """
        stmt = (
            select(ResourceChunk)
            .where(ResourceChunk.resource_id == resource_id)
            .order_by(ResourceChunk.chunk_index)
        )
        return list(self.session.execute(stmt).scalars().all())

    def delete_by_resource_id(
        self, resource_id: uuid.UUID, hard: bool = False
    ) -> int:
        """刪除資源的 chunks（預設軟刪除，T2-A）。

        Args:
            resource_id: Resource UUID。
            hard: True 時走硬刪除（用於需要 re-embed 並整批替換的重處理情境）；
                False（預設）走軟刪除，將 ``is_deleted`` 設為 True 並寫入
                ``deleted_at``。

        Returns:
            受影響的 row 數量。
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
        """以 pgvector cosine distance 進行向量相似度檢索。

        安全性：限制在 ``resource_ids`` 範圍內，避免使用者跨資源檢索他人文件。

        Tier 1（掌握度感知）：當提供 ``user_id`` 且 ``exclude_mastered=True``，
        會 LEFT JOIN ``node_mastery`` 並排除使用者已 MASTERED 的節點。
        沒有對應 node_mastery 紀錄的 chunk（未見內容或新使用者）會保留，
        對冷啟動友善。

        Args:
            query_embedding: 查詢向量（list of float）。
            resource_ids: 限制檢索範圍的 Resource UUID 清單；空 list 直接回傳空結果。
            top_k: 回傳筆數上限，預設 10。
            user_id: 使用者 UUID；提供時啟用掌握度過濾。可為 None。
            exclude_mastered: 是否排除已 MASTERED 節點，預設 True。

        Returns:
            list of dict，每筆為 ``{"chunk": ResourceChunk, "distance": float}``，
            依 distance 升冪排序。``resource_ids`` 為空時回傳空 list。
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
