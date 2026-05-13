"""UserNoteService — 使用者自由格式筆記 CRUD。

Feature 50：我的筆記整合。

業務規則：
- content 不可為空（DB CHECK + service 二次防護）
- 只能操作自己的筆記（user_id 驗證）
- subject_id 必須存在（FK constraint），service 預先驗證避免 DB 例外
- node_id 可選（NULL = 科目層級自由筆記）
- 列表預設依 updated_at DESC 排序
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.knowledge_node import KnowledgeNode
from app.models.subject import Subject
from app.models.user_note import UserNote
from app.services.base import BaseService


class UserNoteService(BaseService):
    """管理 user_notes 的 CRUD 操作。"""

    def __init__(self, db: Session):
        super().__init__(db)

    # ── Create ──────────────────────────────────────────────────────

    def create(
        self,
        *,
        user_id: UUID,
        subject_id: UUID,
        node_id: UUID | None = None,
        title: str | None = None,
        content: str,
    ) -> dict:
        """建立一筆筆記。

        Validations:
        1. content 不可為空
        2. subject_id 必須存在
        3. node_id（若提供）必須存在且屬於該 subject
        """
        # 1. content 不可為空（service 二次防護）
        if not content or not content.strip():
            return self.error("content 不可為空", 422)

        # 2. subject 存在性
        subject = self.db.get(Subject, subject_id)
        if not subject:
            return self.error("科目不存在", 404)

        # 3. node_id 存在性（若提供）
        if node_id is not None:
            node = self.db.get(KnowledgeNode, node_id)
            if not node:
                return self.error("知識節點不存在", 404)
            if node.subject_id != subject_id:
                return self.error("知識節點不屬於指定科目", 422)

        note = UserNote(
            user_id=user_id,
            subject_id=subject_id,
            node_id=node_id,
            title=title.strip() if title else None,
            content=content.strip(),
        )
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return self.ok({"note": note})

    # ── List ────────────────────────────────────────────────────────

    def list(
        self,
        *,
        user_id: UUID,
        subject_id: UUID | None = None,
        node_id: UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """列出自己的筆記（可 filter by subject/node），依 updated_at DESC 排序。"""
        query = self.db.query(UserNote).filter(UserNote.user_id == user_id)

        if subject_id is not None:
            query = query.filter(UserNote.subject_id == subject_id)
        if node_id is not None:
            query = query.filter(UserNote.node_id == node_id)

        total = query.count()
        items = (
            query.order_by(UserNote.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return self.ok({"items": items, "total": total})

    # ── Update ──────────────────────────────────────────────────────

    def update(
        self,
        *,
        note_id: UUID,
        user_id: UUID,
        title: str | None = None,
        content: str | None = None,
    ) -> dict:
        """更新自己的筆記（至少提供 title 或 content 其中之一）。

        - 若 content 提供但為空字串 → 422
        - 不是自己的筆記 → 403
        - 不存在 → 404
        """
        note = self.db.get(UserNote, note_id)
        if not note:
            return self.error("筆記不存在", 404)
        if note.user_id != user_id:
            return self.error("無權限修改他人的筆記", 403)

        # 至少提供一個欄位
        if title is None and content is None:
            return self.error("至少提供 title 或 content 其中之一", 422)

        # content 不可更新為空
        if content is not None:
            stripped = content.strip()
            if not stripped:
                return self.error("content 不可為空", 422)
            note.content = stripped

        if title is not None:
            note.title = title.strip() if title.strip() else None

        note.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(note)
        return self.ok({"note": note})

    # ── Delete ──────────────────────────────────────────────────────

    def delete(self, *, note_id: UUID, user_id: UUID) -> dict:
        """刪除自己的筆記。

        - 不存在 → 404
        - 不是自己的 → 403
        """
        note = self.db.get(UserNote, note_id)
        if not note:
            return self.error("筆記不存在", 404)
        if note.user_id != user_id:
            return self.error("無權限刪除他人的筆記", 403)

        self.db.delete(note)
        self.db.commit()
        return self.ok()
