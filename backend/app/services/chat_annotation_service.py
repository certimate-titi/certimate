"""ChatAnnotationService — AI 教練對話 highlight + 評語管理。

業務規則：
- user_annotation 最少 10 字（API 層 + service 層雙重防護）
- annotation_type 必須在合法 enum 範圍
- 只能對自己的 session 標記（session.user_id == user_id）
- message_id 必須存在且屬於 session_id
- 同 session 同 user 最多 5 筆，超過 409
- 只能刪除自己的 annotation（非自己 → 403）
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.ai_chat import AiChatMessage, AiChatSession
from app.models.chat_annotation_tag import ChatAnnotationTag
from app.models.chat_message_annotation import ChatMessageAnnotation
from app.schemas.chat_annotation import VALID_ANNOTATION_TYPES
from app.services.base import BaseService
from app.utils.markdown_hashtags import extract_hashtags

MAX_ANNOTATIONS_PER_SESSION = 5


class ChatAnnotationService(BaseService):
    """管理 chat_message_annotations 的 CRUD 操作（含 hashtag tag 同步）。"""

    def __init__(self, db: Session):
        super().__init__(db)

    # ── Private: tag sync ───────────────────────────────────────────

    def _sync_annotation_tags(self, annotation: ChatMessageAnnotation, user_annotation_text: str) -> None:
        """從 user_annotation 解析 hashtag 並增量同步 chat_annotation_tags。

        增量策略：
        1. 計算 new_tags set（normalized）
        2. 刪除不再出現的 tags（old - new）
        3. 新增新出現的 tags（new - old）
        4. 已存在的 tags 不修改 tag_display（保留首次輸入）
        """
        new_pairs = extract_hashtags(user_annotation_text)
        new_normalized: set[str] = {n for n, _ in new_pairs}

        # 取得現有 tags
        existing = (
            self.db.query(ChatAnnotationTag)
            .filter(ChatAnnotationTag.annotation_id == annotation.id)
            .all()
        )
        old_normalized: set[str] = {t.tag_normalized for t in existing}

        # 刪除消失的 tags
        to_delete = old_normalized - new_normalized
        if to_delete:
            self.db.query(ChatAnnotationTag).filter(
                ChatAnnotationTag.annotation_id == annotation.id,
                ChatAnnotationTag.tag_normalized.in_(to_delete),
            ).delete(synchronize_session=False)

        # 新增出現的 tags
        to_add = new_normalized - old_normalized
        for normalized, display in new_pairs:
            if normalized in to_add:
                self.db.add(
                    ChatAnnotationTag(
                        annotation_id=annotation.id,
                        tag_normalized=normalized,
                        tag_display=display,
                    )
                )

    # ── Create ──────────────────────────────────────────────────────

    def create_annotation(
        self,
        *,
        message_id: UUID,
        user_id: UUID,
        session_id: UUID,
        highlighted_text: str,
        user_annotation: str,
        annotation_type: str = "note",
    ) -> dict:
        """建立一筆 annotation。

        Validations (按順序):
        1. annotation_type 合法性
        2. user_annotation 長度 ≥ 10
        3. session 存在 + 屬於此 user
        4. message 存在 + 屬於此 session
        5. max=5 per (session, user) 守門
        """
        # 1. annotation_type 合法性
        if annotation_type not in VALID_ANNOTATION_TYPES:
            return self.error(
                f"annotation_type 無效：{annotation_type}，合法值為 {sorted(VALID_ANNOTATION_TYPES)}",
                422,
            )

        # 2. user_annotation 長度（service 二次防護）
        if len(user_annotation) < 10:
            return self.error("user_annotation 最少 10 個字元", 422)

        # 3. 驗 session 存在 + 屬於 user
        session = (
            self.db.query(AiChatSession)
            .filter(AiChatSession.id == session_id)
            .first()
        )
        if not session:
            return self.error("對話 session 不存在", 404)
        if session.user_id != user_id:
            return self.error("無權限標記他人的對話", 403)

        # 4. 驗 message 存在 + 屬於此 session
        message = (
            self.db.query(AiChatMessage)
            .filter(
                AiChatMessage.id == message_id,
                AiChatMessage.session_id == session_id,
            )
            .first()
        )
        if not message:
            return self.error("訊息不存在或不屬於此 session", 404)

        # 5. max=5 守門
        count = (
            self.db.query(ChatMessageAnnotation)
            .filter(
                ChatMessageAnnotation.session_id == session_id,
                ChatMessageAnnotation.user_id == user_id,
            )
            .count()
        )
        if count >= MAX_ANNOTATIONS_PER_SESSION:
            return self.error(
                f"該對話已標記上限（最多 {MAX_ANNOTATIONS_PER_SESSION} 筆）",
                409,
            )

        # 建立
        annotation = ChatMessageAnnotation(
            message_id=message_id,
            user_id=user_id,
            session_id=session_id,
            highlighted_text=highlighted_text,
            user_annotation=user_annotation,
            annotation_type=annotation_type,
        )
        self.db.add(annotation)
        self.db.flush()  # 取得 annotation.id 後再同步 tags

        # 解析並同步 hashtag tags
        self._sync_annotation_tags(annotation, user_annotation)

        self.db.commit()
        self.db.refresh(annotation)
        return self.ok({"annotation": annotation})

    # ── List ────────────────────────────────────────────────────────

    def list_annotations(
        self,
        *,
        user_id: UUID,
        session_id: UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """列出自己的 annotations（可選 filter by session）。"""
        query = self.db.query(ChatMessageAnnotation).filter(
            ChatMessageAnnotation.user_id == user_id
        )
        if session_id is not None:
            query = query.filter(ChatMessageAnnotation.session_id == session_id)

        total = query.count()
        items = (
            query.order_by(ChatMessageAnnotation.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return self.ok({"items": items, "total": total})

    # ── Update ──────────────────────────────────────────────────────

    def update_annotation(
        self,
        *,
        annotation_id: UUID,
        user_id: UUID,
        user_annotation: str | None = None,
        annotation_type: str | None = None,
    ) -> dict:
        """更新自己的 annotation（user_annotation / annotation_type 至少一個）。

        - 不存在 → 404
        - 他人的 → 403
        - user_annotation 若提供必須 ≥ 10 字
        - annotation_type 若提供必須在合法 enum 範圍
        """
        if user_annotation is None and annotation_type is None:
            return self.error("至少提供 user_annotation 或 annotation_type 其中之一", 422)

        annotation = (
            self.db.query(ChatMessageAnnotation)
            .filter(ChatMessageAnnotation.id == annotation_id)
            .first()
        )
        if not annotation:
            return self.error("annotation 不存在", 404)
        if annotation.user_id != user_id:
            return self.error("無權限修改他人的 annotation", 403)

        if user_annotation is not None:
            if len(user_annotation) < 10:
                return self.error("user_annotation 最少 10 個字元", 422)
            annotation.user_annotation = user_annotation

        if annotation_type is not None:
            if annotation_type not in VALID_ANNOTATION_TYPES:
                return self.error(
                    f"annotation_type 無效：{annotation_type}，合法值為 {sorted(VALID_ANNOTATION_TYPES)}",
                    422,
                )
            annotation.annotation_type = annotation_type

        # 若 user_annotation 有更新，重新同步 hashtag tags
        if user_annotation is not None:
            self._sync_annotation_tags(annotation, annotation.user_annotation)

        self.db.commit()
        self.db.refresh(annotation)
        return self.ok({"annotation": annotation})

    # ── Delete All ──────────────────────────────────────────────────

    def delete_all_for_user(self, *, user_id: UUID) -> dict:
        """刪除指定 user 的所有 chat_message_annotations，回傳刪除筆數。"""
        deleted = (
            self.db.query(ChatMessageAnnotation)
            .filter(ChatMessageAnnotation.user_id == user_id)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return self.ok({"deleted": deleted})

    # ── Delete ──────────────────────────────────────────────────────

    def delete_annotation(self, *, annotation_id: UUID, user_id: UUID) -> dict:
        """刪除自己的 annotation（他人的 → 403）。"""
        annotation = (
            self.db.query(ChatMessageAnnotation)
            .filter(ChatMessageAnnotation.id == annotation_id)
            .first()
        )
        if not annotation:
            return self.error("annotation 不存在", 404)
        if annotation.user_id != user_id:
            return self.error("無權限刪除他人的 annotation", 403)

        self.db.delete(annotation)
        self.db.commit()
        return self.ok()
