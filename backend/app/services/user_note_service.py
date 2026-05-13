"""UserNoteService — 使用者自由格式筆記 CRUD + hashtag tag 同步。

Feature 50：我的筆記整合。
Feature 52：筆記 hashtag 系統。
Feature 53：Obsidian-compat markdown export。

業務規則：
- content 不可為空（DB CHECK + service 二次防護）
- 只能操作自己的筆記（user_id 驗證）
- subject_id 必須存在（FK constraint），service 預先驗證避免 DB 例外
- node_id 可選（NULL = 科目層級自由筆記）
- 列表預設依 updated_at DESC 排序
- create/update 自動從 content 解析 hashtag 並同步 user_note_tags
- update 時 diff old vs new tag set，增量更新（不 delete-all-insert-all）
- export_obsidian_zip：考後 30 天才能匯出（force=True 可繞過）
"""

import io
import re
import zipfile
from collections import defaultdict
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.chat_annotation_tag import ChatAnnotationTag
from app.models.chat_message_annotation import ChatMessageAnnotation
from app.models.knowledge_node import KnowledgeNode
from app.models.learning_journey import LearningJourney
from app.models.resource import Resource
from app.models.resource_scaffold import ResourceScaffold
from app.models.scaffold_tag import ScaffoldTag
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

        # 查詢現有 tags（note_id 為 UUID 類型）
        existing_tags = (
            self.db.query(UserNoteTag)
            .filter(UserNoteTag.note_id == note.id)
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
                note_id=note.id,
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
            # 只回含此 tag 的 notes（UserNote.id 和 UserNoteTag.note_id 都是 UUID）
            query = query.join(
                UserNoteTag,
                UserNote.id == UserNoteTag.note_id,
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

        # UserNote.id 和 UserNoteTag.note_id 都是 UUID(as_uuid=True)，直接比較
        query = (
            self.db.query(
                UserNoteTag.tag_normalized,
                UserNoteTag.tag_display,
                func.count(UserNoteTag.note_id).label("count"),
            )
            .join(UserNote, UserNote.id == UserNoteTag.note_id)
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
        query = (
            self.db.query(UserNote)
            .join(
                UserNoteTag,
                UserNote.id == UserNoteTag.note_id,
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

    # ── Obsidian Export ─────────────────────────────────────────────

    def export_obsidian_zip(self, *, user_id: UUID, force: bool = False) -> dict:
        """將 user 的所有 notes + chat annotations + scaffold responses 打包成 Obsidian-compatible ZIP bytes。

        B2 限制：只有考後 30 天才能匯出（任一科目的 learning_journey.exam_date + 30 days < now）。
        若 user 還在備考期（或尚無 exam_date）且 force=False → 403。

        ZIP 結構：
        - note-<title_or_id>.md      每筆 user note（frontmatter: source: note）
        - annotation-<id>.md         每筆 chat annotation（frontmatter: source: annotation）
        - scaffold-<id>.md           每筆 scaffold user_response（frontmatter: source: scaffold）
        - index.md                   整合 3 sources 的 tag 索引（含 count breakdown）

        Args:
            user_id: 匯出者 UUID
            force: True 表示繞過備考期限制

        Returns:
            {"zip_bytes": bytes} 或 {"error": True, "status_code": 403, "message": ...}
        """
        if not force:
            allowed = self._check_export_allowed(user_id)
            if not allowed:
                return self.error("考後 30 天才能匯出避免影響當下複習", 403)

        # ── Source 1: user_notes ────────────────────────────────────
        notes = (
            self.db.query(UserNote)
            .filter(UserNote.user_id == user_id)
            .order_by(UserNote.created_at.asc())
            .all()
        )

        # 預先載入 note tags
        note_ids = [n.id for n in notes]
        tags_by_note: dict[UUID, list[UserNoteTag]] = defaultdict(list)
        if note_ids:
            note_tag_rows = (
                self.db.query(UserNoteTag)
                .filter(UserNoteTag.note_id.in_(note_ids))
                .all()
            )
            for tag in note_tag_rows:
                tags_by_note[tag.note_id].append(tag)

        # ── Source 2: chat_annotations ──────────────────────────────
        annotations = (
            self.db.query(ChatMessageAnnotation)
            .filter(ChatMessageAnnotation.user_id == user_id)
            .order_by(ChatMessageAnnotation.created_at.asc())
            .all()
        )

        annotation_ids = [a.id for a in annotations]
        tags_by_annotation: dict[UUID, list[ChatAnnotationTag]] = defaultdict(list)
        if annotation_ids:
            ann_tag_rows = (
                self.db.query(ChatAnnotationTag)
                .filter(ChatAnnotationTag.annotation_id.in_(annotation_ids))
                .all()
            )
            for tag in ann_tag_rows:
                tags_by_annotation[tag.annotation_id].append(tag)

        # ── Source 3: scaffold user_responses ───────────────────────
        scaffold_tag_rows = (
            self.db.query(ScaffoldTag)
            .filter(ScaffoldTag.user_id == user_id)
            .all()
        )
        scaffold_ids_with_tags = list({st.scaffold_id for st in scaffold_tag_rows})

        scaffolds: list[ResourceScaffold] = []
        if scaffold_ids_with_tags:
            scaffolds = (
                self.db.query(ResourceScaffold)
                .filter(
                    ResourceScaffold.id.in_(scaffold_ids_with_tags),
                    ResourceScaffold.user_response.isnot(None),
                )
                .order_by(ResourceScaffold.created_at.asc())
                .all()
            )

        tags_by_scaffold: dict[UUID, list[ScaffoldTag]] = defaultdict(list)
        for st in scaffold_tag_rows:
            tags_by_scaffold[st.scaffold_id].append(st)

        # 取得 scaffold 對應 resource 的 subject_id
        resource_ids = list({s.resource_id for s in scaffolds if s.resource_id})
        resources_map: dict[UUID, Resource] = {}
        if resource_ids:
            resources = self.db.query(Resource).filter(Resource.id.in_(resource_ids)).all()
            resources_map = {r.id: r for r in resources}

        # 收集所有需要查 subject 的 id（notes + resources）
        subject_ids_all: set[UUID] = {n.subject_id for n in notes}
        for r in resources_map.values():
            if r.subject_id:
                subject_ids_all.add(r.subject_id)

        subjects_map: dict[UUID, Subject] = {}
        if subject_ids_all:
            subjects = self.db.query(Subject).filter(Subject.id.in_(subject_ids_all)).all()
            subjects_map = {s.id: s for s in subjects}

        # ── 構建 ZIP ──────────────────────────────────────────────────
        buf = io.BytesIO()
        # tag_display → [{filename, title, source}] 用於 index.md
        tag_index: dict[str, list[dict]] = defaultdict(list)
        filenames_used: dict[str, int] = {}

        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            # Source 1: notes（檔名前綴 note-）
            for note in notes:
                filename = "note-" + self._safe_filename(note, filenames_used)
                subject = subjects_map.get(note.subject_id)
                note_tags = tags_by_note.get(note.id, [])

                md_content = self._build_note_md(note, subject, note_tags)
                zf.writestr(filename, md_content)

                display_title = note.title or str(note.id)
                for tag in note_tags:
                    tag_index[tag.tag_display].append(
                        {"filename": filename, "title": display_title, "source": "note"}
                    )

            # Source 2: chat annotations（檔名前綴 annotation-）
            for annotation in annotations:
                ann_id_str = str(annotation.id)
                filename = f"annotation-{ann_id_str}.md"
                ann_tags = tags_by_annotation.get(annotation.id, [])

                md_content = self._build_annotation_md(annotation, ann_tags)
                zf.writestr(filename, md_content)

                for tag in ann_tags:
                    tag_index[tag.tag_display].append(
                        {
                            "filename": filename,
                            "title": f"Annotation {ann_id_str[:8]}",
                            "source": "annotation",
                        }
                    )

            # Source 3: scaffold responses（檔名前綴 scaffold-）
            for scaffold in scaffolds:
                scaffold_id_str = str(scaffold.id)
                filename = f"scaffold-{scaffold_id_str}.md"
                sc_tags = tags_by_scaffold.get(scaffold.id, [])

                resource = resources_map.get(scaffold.resource_id) if scaffold.resource_id else None
                subject = (
                    subjects_map.get(resource.subject_id)
                    if resource and resource.subject_id
                    else None
                )

                md_content = self._build_scaffold_md(scaffold, subject, sc_tags)
                zf.writestr(filename, md_content)

                for tag in sc_tags:
                    tag_index[tag.tag_display].append(
                        {
                            "filename": filename,
                            "title": f"Scaffold {scaffold_id_str[:8]}",
                            "source": "scaffold",
                        }
                    )

            # 寫入 index.md（整合 3 sources）
            index_md = self._build_index_md(tag_index)
            zf.writestr("index.md", index_md)

        zip_bytes = buf.getvalue()
        return self.ok({"zip_bytes": zip_bytes})

    # ── Private: export helpers ─────────────────────────────────────

    def _check_export_allowed(self, user_id: UUID) -> bool:
        """判斷是否允許匯出：任一 learning_journey.exam_date + 30 days < today。

        若 user 完全沒有 exam_date 設定 → 不允許（保守策略）。
        只要有任一科目已通過 30 天緩衝期 → 允許。
        """
        today = date.today()
        journeys = (
            self.db.query(LearningJourney)
            .filter(LearningJourney.user_id == user_id)
            .filter(LearningJourney.exam_date.isnot(None))
            .all()
        )

        if not journeys:
            return False

        for journey in journeys:
            if journey.exam_date is not None:
                days_since_exam = (today - journey.exam_date).days
                if days_since_exam > 30:
                    return True

        return False

    def _safe_filename(self, note: UserNote, used: dict[str, int]) -> str:
        """從 title 或 id 產生安全的 .md 檔名（去除特殊字元，處理重複）。"""
        base = note.title if note.title else str(note.id)
        # 去除路徑分隔符號與 YAML 特殊字元
        safe = re.sub(r'[\\/:*?"<>|#\[\]]', "_", base).strip()
        if not safe:
            safe = str(note.id)
        filename = f"{safe}.md"

        # 處理重名
        if filename in used:
            used[filename] += 1
            filename = f"{safe}_{used[filename]}.md"
        else:
            used[filename] = 0

        return filename

    def _build_note_md(
        self,
        note: UserNote,
        subject: "Subject | None",
        tags: "list[UserNoteTag]",
    ) -> str:
        """組裝單筆 note 的 markdown 文字（YAML frontmatter + content）。"""
        subject_name = subject.name if subject else ""
        node_id_str = str(note.node_id) if note.node_id else ""
        created_at_iso = note.created_at.isoformat() if note.created_at else ""
        updated_at_iso = note.updated_at.isoformat() if note.updated_at else ""

        frontmatter_lines = [
            "---",
            f"id: {note.id}",
            f"subject_id: {note.subject_id}",
            f"subject_name: {subject_name}",
            f"node_id: {node_id_str}",
            f"created_at: {created_at_iso}",
            f"updated_at: {updated_at_iso}",
            "---",
        ]
        frontmatter = "\n".join(frontmatter_lines)
        return f"{frontmatter}\n\n{note.content}\n"

    def _build_annotation_md(
        self,
        annotation: "ChatMessageAnnotation",
        tags: "list[ChatAnnotationTag]",
    ) -> str:
        """組裝 chat annotation 的 markdown 文字（YAML frontmatter + content）。"""
        created_at_iso = annotation.created_at.isoformat() if annotation.created_at else ""
        tag_list = ", ".join(f"#{t.tag_display}" for t in tags) if tags else ""

        frontmatter_lines = [
            "---",
            f"id: {annotation.id}",
            "source: annotation",
            f"annotation_type: {annotation.annotation_type}",
            f"created_at: {created_at_iso}",
            f"tags: [{tag_list}]",
            "---",
        ]
        frontmatter = "\n".join(frontmatter_lines)
        highlighted = annotation.highlighted_text or ""
        user_ann = annotation.user_annotation or ""
        return f"{frontmatter}\n\n## Highlighted Text\n\n> {highlighted}\n\n## Annotation\n\n{user_ann}\n"

    def _build_scaffold_md(
        self,
        scaffold: "ResourceScaffold",
        subject: "Subject | None",
        tags: "list[ScaffoldTag]",
    ) -> str:
        """組裝 scaffold user_response 的 markdown 文字（YAML frontmatter + content）。"""
        created_at_iso = scaffold.created_at.isoformat() if scaffold.created_at else ""
        responded_at_iso = scaffold.responded_at.isoformat() if scaffold.responded_at else ""
        subject_name = subject.name if subject else ""
        tag_list = ", ".join(f"#{t.tag_display}" for t in tags) if tags else ""

        frontmatter_lines = [
            "---",
            f"id: {scaffold.id}",
            "source: scaffold",
            f"scaffold_type: {scaffold.type}",
            f"chapter_heading: {scaffold.chapter_heading or ''}",
            f"subject_name: {subject_name}",
            f"created_at: {created_at_iso}",
            f"responded_at: {responded_at_iso}",
            f"tags: [{tag_list}]",
            "---",
        ]
        frontmatter = "\n".join(frontmatter_lines)
        content = scaffold.content or ""
        user_response = scaffold.user_response or ""
        return f"{frontmatter}\n\n## Question\n\n{content}\n\n## My Response\n\n{user_response}\n"

    def _build_index_md(self, tag_index: "dict[str, list[dict]]") -> str:
        """組裝 index.md：整合 3 sources 的 tag 索引（含 count breakdown）。"""
        lines = ["# Notes Index (3 Sources)", ""]
        if not tag_index:
            lines.append("_No tags found._")
            lines.append("")
        else:
            for tag_display in sorted(tag_index.keys()):
                items = tag_index[tag_display]
                note_count = sum(1 for i in items if i.get("source") == "note")
                ann_count = sum(1 for i in items if i.get("source") == "annotation")
                sc_count = sum(1 for i in items if i.get("source") == "scaffold")
                total = len(items)
                lines.append(
                    f"## #{tag_display} ({total} — note:{note_count} annotation:{ann_count} scaffold:{sc_count})"
                )
                for item in items:
                    link = item["filename"].replace(".md", "")
                    title = item["title"]
                    source = item.get("source", "note")
                    lines.append(f"- [{source}] [[{link}|{title}]]")
                lines.append("")
        return "\n".join(lines)
