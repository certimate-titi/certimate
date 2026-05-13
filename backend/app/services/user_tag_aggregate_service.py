"""UserTagAggregateService — 跨 3 sources 的 tag 聚合查詢服務。

Feature 54：tag 系統涵蓋 3 sources（user_notes / chat_annotations / scaffold user_response）

Sources:
- user_note_tags        → 透過 user_notes.user_id / subject_id filter
- chat_annotation_tags  → 透過 chat_message_annotations.user_id filter（無直接 subject_id）
- scaffold_tags         → 透過 scaffold_tags.user_id / resource_scaffolds.resource_id → resources.subject_id filter

Aggregate endpoint 回傳：
  {
    "items": [
      {"normalized": "ai", "display": "AI", "count": 8, "sources": {"note": 5, "annotation": 2, "scaffold": 1}},
      ...
    ],
    "total": N
  }
"""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.base import BaseService


class UserTagAggregateService(BaseService):
    """跨 3 sources 的 tag 聚合查詢。"""

    def __init__(self, db: Session):
        super().__init__(db)

    def aggregate_tags(
        self,
        *,
        user_id: UUID,
        subject_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """聚合 3 sources 的 unique tags，支援 subject_id filter。

        UNION ALL 三張 tag 表後 GROUP BY 計算 count 與 sources breakdown。

        subject_id filter：
        - note：user_notes.subject_id = subject_id
        - annotation：chat_message_annotations 無直接 subject_id，不 filter（回傳全部）
        - scaffold：scaffold_tags → resource_scaffolds → resources.subject_id = subject_id

        Args:
            user_id: 查詢者 UUID
            subject_id: 可選科目過濾
            limit: 分頁大小（預設 50）
            offset: 分頁偏移

        Returns:
            {"items": [...], "total": N}
        """
        user_id_str = str(user_id)
        subject_id_str = str(subject_id) if subject_id else None

        # 構建 UNION ALL SQL
        # source 1: user_note_tags
        note_cte = """
            SELECT
                unt.tag_normalized,
                unt.tag_display,
                'note'::text AS source
            FROM user_note_tags unt
            JOIN user_notes un ON un.id = unt.note_id
            WHERE un.user_id = :user_id
            {note_subject_filter}
        """
        if subject_id:
            note_cte = note_cte.format(note_subject_filter="AND un.subject_id = :subject_id")
        else:
            note_cte = note_cte.format(note_subject_filter="")

        # source 2: chat_annotation_tags（無 subject_id，不 filter）
        annotation_cte = """
            SELECT
                cat.tag_normalized,
                cat.tag_display,
                'annotation'::text AS source
            FROM chat_annotation_tags cat
            JOIN chat_message_annotations cma ON cma.id = cat.annotation_id
            WHERE cma.user_id = :user_id
        """

        # source 3: scaffold_tags
        scaffold_cte = """
            SELECT
                st.tag_normalized,
                st.tag_display,
                'scaffold'::text AS source
            FROM scaffold_tags st
            WHERE st.user_id = :user_id
            {scaffold_subject_filter}
        """
        if subject_id:
            scaffold_cte = scaffold_cte.format(
                scaffold_subject_filter="""
                AND st.scaffold_id IN (
                    SELECT rs.id FROM resource_scaffolds rs
                    JOIN resources r ON r.id = rs.resource_id
                    WHERE r.subject_id = :subject_id
                )
                """
            )
        else:
            scaffold_cte = scaffold_cte.format(scaffold_subject_filter="")

        # 最終聚合 SQL
        sql = f"""
            WITH all_tags AS (
                {note_cte}
                UNION ALL
                {annotation_cte}
                UNION ALL
                {scaffold_cte}
            ),
            aggregated AS (
                SELECT
                    tag_normalized,
                    MIN(tag_display) AS display,
                    COUNT(*) AS total_count,
                    COUNT(*) FILTER (WHERE source = 'note') AS note_count,
                    COUNT(*) FILTER (WHERE source = 'annotation') AS annotation_count,
                    COUNT(*) FILTER (WHERE source = 'scaffold') AS scaffold_count
                FROM all_tags
                GROUP BY tag_normalized
            )
            SELECT *
            FROM aggregated
            ORDER BY total_count DESC, tag_normalized ASC
        """

        params: dict = {"user_id": user_id_str}
        if subject_id:
            params["subject_id"] = subject_id_str

        rows = self.db.execute(text(sql), params).fetchall()

        total = len(rows)
        paged = rows[offset : offset + limit]

        items = [
            {
                "normalized": row.tag_normalized,
                "display": row.display,
                "count": row.total_count,
                "sources": {
                    "note": row.note_count,
                    "annotation": row.annotation_count,
                    "scaffold": row.scaffold_count,
                },
            }
            for row in paged
        ]

        return self.ok({"items": items, "total": total})

    def items_by_tag(
        self,
        *,
        user_id: UUID,
        tag: str,
        subject_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """回傳指定 tag 下所有 3 sources 的混合 items。

        每個 item 含：
        - _kind: note | annotation | scaffold
        - _id: item UUID
        - content: 內容片段（最多 500 字）
        - subject_id（若有）
        - created_at

        Args:
            user_id: 查詢者 UUID
            tag: normalized tag（lowercase）
            subject_id: 可選科目過濾
            limit: 分頁大小
            offset: 分頁偏移

        Returns:
            {"items": [...], "total": N}
        """
        user_id_str = str(user_id)
        tag_normalized = tag.lower().strip()
        subject_id_str = str(subject_id) if subject_id else None

        note_subject_filter = "AND un.subject_id = :subject_id" if subject_id else ""
        scaffold_subject_filter = """
            AND st.scaffold_id IN (
                SELECT rs.id FROM resource_scaffolds rs
                JOIN resources r ON r.id = rs.resource_id
                WHERE r.subject_id = :subject_id
            )
        """ if subject_id else ""

        sql = f"""
            WITH items AS (
                -- notes
                SELECT
                    'note'::text AS _kind,
                    un.id AS _id,
                    LEFT(un.content, 500) AS content,
                    un.subject_id,
                    un.created_at
                FROM user_note_tags unt
                JOIN user_notes un ON un.id = unt.note_id
                WHERE un.user_id = :user_id
                  AND unt.tag_normalized = :tag
                {note_subject_filter}

                UNION ALL

                -- chat annotations
                SELECT
                    'annotation'::text AS _kind,
                    cma.id AS _id,
                    LEFT(cma.user_annotation, 500) AS content,
                    NULL::uuid AS subject_id,
                    cma.created_at
                FROM chat_annotation_tags cat
                JOIN chat_message_annotations cma ON cma.id = cat.annotation_id
                WHERE cma.user_id = :user_id
                  AND cat.tag_normalized = :tag

                UNION ALL

                -- scaffold responses
                SELECT
                    'scaffold'::text AS _kind,
                    rs.id AS _id,
                    LEFT(rs.user_response, 500) AS content,
                    r.subject_id,
                    rs.responded_at AS created_at
                FROM scaffold_tags st
                JOIN resource_scaffolds rs ON rs.id = st.scaffold_id
                LEFT JOIN resources r ON r.id = rs.resource_id
                WHERE st.user_id = :user_id
                  AND st.tag_normalized = :tag
                {scaffold_subject_filter}
            )
            SELECT *
            FROM items
            ORDER BY created_at DESC NULLS LAST
        """

        params: dict = {"user_id": user_id_str, "tag": tag_normalized}
        if subject_id:
            params["subject_id"] = subject_id_str

        rows = self.db.execute(text(sql), params).fetchall()

        total = len(rows)
        paged = rows[offset : offset + limit]

        items = [
            {
                "_kind": row._kind,
                "_id": str(row._id),
                "content": row.content,
                "subject_id": str(row.subject_id) if row.subject_id else None,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in paged
        ]

        return self.ok({"items": items, "total": total})
