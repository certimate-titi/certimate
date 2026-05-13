"""UserNoteService — 使用者自由格式筆記 CRUD + hashtag tag 同步。

Feature 50：我的筆記整合。
Feature 52：筆記 hashtag 系統。

業務規則：
- content 不可為空（DB CHECK + service 二次防護）
- 只能操作自己的筆記（user_id 驗證）
- subject_id 必須存在（FK constraint），service 預先驗證避免 DB 例外
- node_id 可選（NULL = 科目層級自由筆記）
- 列表預設依 updated_at DESC 排序
- create/update 自動從 content 解析 hashtag 並同步 user_note_tags
- update 時 diff old vs new tag set，增量更新（不 delete-all-insert-all）
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.knowledge_node import KnowledgeNode
from app.models.subject import Subject
from app.models.user_note import UserNote
from app.models.user_note_tag import UserNoteTag
from app.services.base import BaseService
from app.utils.markdown_hashtags import extract_hashtags


class UserNoteService(BaseService):
    """管理 user_notes 的 CRUD 操作 + hashtag tag 同步。"""

    def __init__(self, db: Session):
        super().__init__(db)

    # ── Private: tag sync ───────────────────────────────────────────

    def _sync_tags(self, note: UserNote, content: str) -> None:
        """從 content 解析 hashtag 並增量同步 user_note_tags。

        增量策略：
        1. 計算 new_tags set（normalized）
        2. 刪除不再出現的 tags（old - new）
        3. 新增新出現的 tags（new - old）
        4. 保留仍存在的 tags（不動，避免破壞可能的 created_at）

        Args:
            note: UserNote ORM 物件（需已有 id）
            content: 新的筆記內容
        """
        # 解析新 tag 列表
        new_tag_pairs = extract_hashtags(content)
        new_normalized_set = {n for n, _ in new_tag_pairs}
        new_display_map = {n: d for n, d in new_tag_pairs}

        # 查詢現有 tags
        existing_tags = (
            self.db.query(UserNoteTag)
            .filter(UserNoteTag.note_id == str(note.id))
            .all()
        )
        existing_normalized_set = {t.tag_normalized for t in existing_tags}

        # 刪除移除的 tags
        to_remove = existing_normalized_set - new_normalized_set
        if to_remove:
            for tag in existing_tags:
                if tag.tag_normalized in to_remove:
                    self.db.delete(tag)

        # 新增新加的 tags
        to_add = new_normalized_set - existing_normalized_set
        for normalized in to_add:
            display = new_display_map[normalized]
            new_tag = UserNoteTag(
                note_id=str(note.id),
                tag_normalized=normalized,
                tag_display=display,
            )
            self.db.add(new_tag)

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
        """建立一筆筆記，並同步解析 hashtag 至 user_note_tags。

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

        stripped_content = content.strip()
        note = UserNote(
            user_id=user_id,
            subject_id=subject_id,
            node_id=node_id,
            title=title.strip() if title else None,
            content=stripped_content,
        )
        self.db.add(note)
        self.db.flush()  # 取得 note.id 後才能建 tags

        # 同步 hashtag tags
        self._sync_tags(note, stripped_content)

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
        tag: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """列出自己的筆記（可 filter by subject/node/tag），依 updated_at DESC 排序。

        Args:
            tag: 依 tag_normalized 過濾（若提供，只回含此 tag 的 notes）
        """
        query = self.db.query(UserNote).filter(UserNote.user_id == user_id)

        if subject_id is not None:
            query = query.filter(UserNote.subject_id == subject_id)
        if node_id is not None:
            query = query.filter(UserNote.node_id == node_id)
        if tag is not None:
            import sqlalchemy as sa

            # 只回含此 tag 的 notes
            query = query.join(
                UserNoteTag,
                sa.cast(UserNote.id, sa.String) == UserNoteTag.note_id,
            ).filter(UserNoteTag.tag_normalized == tag.lower().strip())

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
        若 content 更新，同步 diff hashtag tags。

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
            # 同步 hashtag tags（增量 diff）
            self._sync_tags(note, stripped)

        if title is not None:
            note.title = title.strip() if title.strip() else None

        note.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(note)
        return self.ok({"note": note})

    # ── Delete All ──────────────────────────────────────────────────

    def delete_all_for_user(self, *, user_id: UUID) -> dict:
        """刪除指定 user 的所有筆記，回傳刪除筆數。"""
        deleted = (
            self.db.query(UserNote)
            .filter(UserNote.user_id == user_id)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return self.ok({"deleted": deleted})

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

    # ── Tag Queries ─────────────────────────────────────────────────

    def list_user_tags(
        self,
        *,
        user_id: UUID,
        subject_id: UUID | None = None,
    ) -> dict:
        """列出該 user 所有 unique tags + count（可選 subject_id 過濾）。

        Args:
            user_id: 擁有者
            subject_id: 若提供，只列該 subject 的 notes 用到的 tags

        Returns:
            {items: [{normalized, display, count}], total: int}
        """
        from sqlalchemy import func

        import sqlalchemy as sa

        query = (
            self.db.query(
                UserNoteTag.tag_normalized,
                UserNoteTag.tag_display,
                func.count(UserNoteTag.note_id).label("count"),
            )
            .join(UserNote, sa.cast(UserNote.id, sa.String) == UserNoteTag.note_id)
            .filter(UserNote.user_id == user_id)
        )

        if subject_id is not None:
            query = query.filter(UserNote.subject_id == subject_id)

        rows = (
            query
            .group_by(UserNoteTag.tag_normalized, UserNoteTag.tag_display)
            .order_by(func.count(UserNoteTag.note_id).desc())
            .all()
        )

        items = [
            {"normalized": r.tag_normalized, "display": r.tag_display, "count": r.count}
            for r in rows
        ]
        return self.ok({"items": items, "total": len(items)})

    def list_notes_by_tag(
        self,
        *,
        user_id: UUID,
        tag_normalized: str,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """列出含指定 tag 的所有 notes（歸屬該 user）。

        Args:
            user_id: 擁有者
            tag_normalized: lowercase tag 字串
            limit: 分頁上限
            offset: 分頁偏移

        Returns:
            {items: [UserNote], total: int}
        """
        import sqlalchemy as sa

        query = (
            self.db.query(UserNote)
            .join(
                UserNoteTag,
                sa.cast(UserNote.id, sa.String) == UserNoteTag.note_id,
            )
            .filter(UserNote.user_id == user_id)
            .filter(UserNoteTag.tag_normalized == tag_normalized.lower().strip())
        )

        total = query.count()
        items = (
            query.order_by(UserNote.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return self.ok({"items": items, "total": total})
