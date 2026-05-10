"""ChapterAnchorService — K-RE-01 章節級讀前定錨生成服務.

針對純逆向工程科目（無教材但有節點 + 考古題），
用考古題群組生成章節級 advance_organizer。

教學原理：Ausubel Subsumption Theory
- advance_organizer 比要學內容抽象一階
- 提供「這一章在考什麼方向」的心智模型
- 章節級（depth=1）優於節點級（depth=2）

設計約束：
- 1 個章節 → 1 個 advance_organizer
- 80 字 hard limit（post-processor 強制截短）
- resource_id = NULL（純逆向工程，無教材資源）
- idempotent：已有 template_code='K-RE-01' + type=advance_organizer → skip
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.historical_exam import HistoricalExam
from app.models.knowledge_node import KnowledgeNode
from app.models.question import Question
from app.models.resource_scaffold import ResourceScaffold, ResourceScaffoldType
from app.models.scaffold_node_link import ScaffoldNodeLink
from app.models.subject import Subject
from app.services.base import BaseService

log = logging.getLogger(__name__)
settings = get_settings()

# ── 常數 ────────────────────────────────────────────────────────────────────
MAX_SAMPLE_QUESTIONS = 8
ADVANCE_ORGANIZER_MAX_CHARS = 80
TEMPLATE_CODE = "K-RE-01"
LLM_MAX_TOKENS = 200

# Gemini 2.5 Pro 估算（輸入：約 400 tokens，輸出：約 50 tokens）
APPROX_INPUT_TOKENS_PER_CHAPTER = 400
APPROX_OUTPUT_TOKENS_PER_CHAPTER = 50
# Gemini 2.5 Pro 定價（2026-05，美元）
GEMINI_INPUT_PRICE_PER_1K = 0.00125
GEMINI_OUTPUT_PRICE_PER_1K = 0.010


class ChapterAnchorService(BaseService):
    """章節級讀前定錨生成 Service（K-RE-01）.

    所有查詢嚴格帶 subject_id 過濾，遵守科目隔離規則。
    """

    # ── 主入口 ──────────────────────────────────────────────────────────────

    def generate_for_subject(self, subject_id: str, dry_run: bool = False) -> dict:
        """遍歷該 subject 所有 depth=1 chapter，每章生成 advance_organizer.

        Args:
            subject_id: 科目 UUID 字串
            dry_run: True 時只估算 token 成本，不呼叫 LLM 也不寫 DB

        Returns:
            self.ok({
                "chapters_processed": int,
                "scaffolds_created": int,
                "links_created": int,
                "skipped_no_questions": int,
                "skipped_already_exists": int,
                "total_cost_usd": float,
                "dry_run": bool,
            })
        """
        try:
            sid = uuid.UUID(subject_id)
        except ValueError:
            return self.error("無效的 subject_id 格式", 400)

        subject = self.db.query(Subject).filter(Subject.id == sid).first()
        if not subject:
            return self.error("科目不存在", 404)

        # 取所有 depth=1 章節
        chapters = (
            self.db.query(KnowledgeNode)
            .filter(
                KnowledgeNode.subject_id == sid,
                KnowledgeNode.depth == 1,
            )
            .order_by(KnowledgeNode.sort_order, KnowledgeNode.created_at)
            .all()
        )

        if not chapters:
            return self.ok({
                "chapters_processed": 0,
                "scaffolds_created": 0,
                "links_created": 0,
                "skipped_no_questions": 0,
                "skipped_already_exists": 0,
                "total_cost_usd": 0.0,
                "dry_run": dry_run,
                "message": "此科目無章節節點（depth=1）",
            })

        stats = {
            "chapters_processed": 0,
            "scaffolds_created": 0,
            "links_created": 0,
            "skipped_no_questions": 0,
            "skipped_already_exists": 0,
        }

        for chapter in chapters:
            result = self._process_chapter(
                subject=subject,
                chapter=chapter,
                dry_run=dry_run,
            )
            stats["chapters_processed"] += 1
            stats["scaffolds_created"] += result.get("scaffolds_created", 0)
            stats["links_created"] += result.get("links_created", 0)
            stats["skipped_no_questions"] += result.get("skipped_no_questions", 0)
            stats["skipped_already_exists"] += result.get("skipped_already_exists", 0)

        # 估算 token 成本（僅計算實際生成的章節）
        generated_count = stats["scaffolds_created"]
        total_input = generated_count * APPROX_INPUT_TOKENS_PER_CHAPTER
        total_output = generated_count * APPROX_OUTPUT_TOKENS_PER_CHAPTER
        cost_usd = (
            (total_input / 1000 * GEMINI_INPUT_PRICE_PER_1K)
            + (total_output / 1000 * GEMINI_OUTPUT_PRICE_PER_1K)
        )

        log.info(
            "K-RE-01 generate_for_subject subject=%s chapters=%d created=%d cost=$%.6f dry_run=%s",
            subject_id,
            stats["chapters_processed"],
            stats["scaffolds_created"],
            cost_usd,
            dry_run,
        )

        return self.ok({
            **stats,
            "total_cost_usd": round(cost_usd, 6),
            "dry_run": dry_run,
        })

    # ── 單章處理 ─────────────────────────────────────────────────────────────

    def _process_chapter(
        self,
        subject: Subject,
        chapter: KnowledgeNode,
        dry_run: bool,
    ) -> dict:
        """處理單一章節的 advance_organizer 生成.

        Returns:
            dict with keys: scaffolds_created, links_created,
                            skipped_no_questions, skipped_already_exists
        """
        # Idempotency：若已有 K-RE-01 advance_organizer 則跳過
        existing = (
            self.db.query(ResourceScaffold)
            .join(ScaffoldNodeLink, ScaffoldNodeLink.scaffold_id == ResourceScaffold.id)
            .filter(
                ScaffoldNodeLink.node_id == chapter.id,
                ResourceScaffold.type == ResourceScaffoldType.ADVANCE_ORGANIZER.value,
                ResourceScaffold.template_code == TEMPLATE_CODE,
            )
            .first()
        )
        if existing:
            log.debug(
                "K-RE-01 skip chapter=%s (already has advance_organizer)", chapter.name
            )
            return {"skipped_already_exists": 1, "scaffolds_created": 0, "links_created": 0, "skipped_no_questions": 0}

        # 取子節點名稱
        child_names = self._get_child_node_names(chapter.id)

        # 取考古題 stems
        question_stems = self._get_chapter_questions(chapter.id, subject)
        if not question_stems:
            log.info(
                "K-RE-01 skip chapter=%s (no questions found)", chapter.name
            )
            return {"skipped_no_questions": 1, "scaffolds_created": 0, "links_created": 0, "skipped_already_exists": 0}

        if dry_run:
            # dry_run：只回報將會處理，不打 LLM 也不寫 DB
            return {"scaffolds_created": 1, "links_created": 0, "skipped_no_questions": 0, "skipped_already_exists": 0}

        # 呼叫 LLM
        content = self._call_llm(
            chapter_name=chapter.name,
            subject_name=subject.name,
            child_names=child_names,
            question_stems=question_stems,
        )
        if content is None:
            log.warning("K-RE-01 LLM 回傳失敗 chapter=%s", chapter.name)
            return {"scaffolds_created": 0, "links_created": 0, "skipped_no_questions": 0, "skipped_already_exists": 0}

        # 80 字 hard limit
        content = _truncate_to_chars(content, ADVANCE_ORGANIZER_MAX_CHARS)

        # 寫入 DB + 建 links
        result = self._persist_and_link(chapter, content)
        return {
            "scaffolds_created": 1 if result else 0,
            "links_created": result.get("links_created", 0) if result else 0,
            "skipped_no_questions": 0,
            "skipped_already_exists": 0,
        }

    # ── 資料查詢 ─────────────────────────────────────────────────────────────

    def _get_child_node_names(self, chapter_id: uuid.UUID) -> list[str]:
        """取得章節下所有 depth=2 子節點名稱."""
        nodes = (
            self.db.query(KnowledgeNode.name)
            .filter(KnowledgeNode.parent_id == chapter_id)
            .order_by(KnowledgeNode.sort_order)
            .all()
        )
        return [row[0] for row in nodes]

    def _get_all_descendant_nodes(self, chapter_id: uuid.UUID) -> list[KnowledgeNode]:
        """取得章節下所有後代節點（depth 1/2/3，包含 chapter 本身）."""
        # 先取直接子節點
        children = (
            self.db.query(KnowledgeNode)
            .filter(KnowledgeNode.parent_id == chapter_id)
            .all()
        )
        result = list(children)
        # 取孫節點（depth+2）
        for child in children:
            grandchildren = (
                self.db.query(KnowledgeNode)
                .filter(KnowledgeNode.parent_id == child.id)
                .all()
            )
            result.extend(grandchildren)
        return result

    def _get_descendant_node_ids(self, chapter_id: uuid.UUID) -> list[uuid.UUID]:
        """章節下所有後代節點 ID（含 chapter 自身），給 Question.node_id FK 查題用."""
        descendants = self._get_all_descendant_nodes(chapter_id)
        ids = [n.id for n in descendants]
        ids.append(chapter_id)
        return ids

    def _get_chapter_questions(
        self,
        chapter_id: uuid.UUID,
        subject: Subject,
    ) -> list[str]:
        """取得章節下所有節點命中的考古題 stems（最多 8 題）.

        策略：取章節下所有子節點名稱，聯集比對 question.content，
        嚴格帶 subject 的 historical_exam_id 過濾（科目隔離）。

        Args:
            chapter_id: 章節節點 UUID
            subject: Subject ORM 物件

        Returns:
            考古題 stem 列表（最多 8 題，已截短）
        """
        he_ids = self._get_historical_exam_ids(subject)
        if not he_ids:
            return []

        # 主路徑：用 Question.node_id FK 找該章後代節點對應的題（與 production
        # available_questions 計算一致；ai_generation_service 也用這個 path）
        descendant_ids = self._get_descendant_node_ids(chapter_id)
        qs = []
        if descendant_ids:
            qs = (
                self.db.query(Question.content)
                .filter(
                    Question.historical_exam_id.in_(he_ids),
                    Question.node_id.in_(descendant_ids),
                )
                .limit(MAX_SAMPLE_QUESTIONS)
                .all()
            )

        # Fallback：若 FK 無 hit（節點還沒 link 到題目），退回 ILIKE 章節+子節點名
        if not qs:
            child_names = self._get_child_node_names(chapter_id)
            if not child_names:
                chapter = self.db.query(KnowledgeNode).filter(KnowledgeNode.id == chapter_id).first()
                if chapter:
                    child_names = [chapter.name]
            content_filters = [
                Question.content.ilike(f"%{name}%")
                for name in child_names
                if name and len(name) >= 2
            ]
            if content_filters:
                qs = (
                    self.db.query(Question.content)
                    .filter(
                        Question.historical_exam_id.in_(he_ids),
                        or_(*content_filters),
                    )
                    .limit(MAX_SAMPLE_QUESTIONS)
                    .all()
                )

        # 取前 120 字作為 stem
        stems = [(row[0] or "")[:120] for row in qs]
        return stems

    def _get_historical_exam_ids(self, subject: Subject) -> list[uuid.UUID]:
        """依 subject.exam_subject_codes 取得對應的 historical_exam id 清單.

        科目隔離：嚴格用 exam_subject_codes 精確匹配，不跨科目。
        """
        he_query = self.db.query(HistoricalExam.id)
        code_filters = []

        if subject.exam_subject_codes:
            for code in subject.exam_subject_codes:
                parts = code.split(":", 1)
                if len(parts) == 2:
                    code_filters.append(and_(
                        HistoricalExam.exam_code == parts[0],
                        HistoricalExam.subject_code == parts[1],
                    ))

        if code_filters:
            he_query = he_query.filter(or_(*code_filters))
        elif subject.name:
            # Fallback：完整科目名稱精確匹配
            he_query = he_query.filter(HistoricalExam.subject_name == subject.name)
        else:
            return []

        return [row[0] for row in he_query.all()]

    # ── LLM 呼叫 ─────────────────────────────────────────────────────────────

    def _call_llm(
        self,
        chapter_name: str,
        subject_name: str,
        child_names: list[str],
        question_stems: list[str],
    ) -> Optional[str]:
        """呼叫 Gemini 2.5 Pro 生成 advance_organizer.

        Args:
            chapter_name: 章節名稱
            subject_name: 科目名稱
            child_names: 子節點名稱清單
            question_stems: 考古題 stem 清單

        Returns:
            advance_organizer 字串（已後處理），失敗回 None
        """
        if not settings.GEMINI_API_KEY:
            log.warning("K-RE-01 GEMINI_API_KEY 未設定，跳過 LLM 呼叫")
            return None

        system_prompt = _build_system_prompt()
        user_prompt = _build_user_prompt(
            subject_name=subject_name,
            chapter_name=chapter_name,
            child_names=child_names,
            question_stems=question_stems,
        )

        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=user_prompt,
                config={
                    "system_instruction": system_prompt,
                    "max_output_tokens": LLM_MAX_TOKENS,
                    "temperature": 0.7,
                },
            )
            raw = (response.text or "").strip()

            # 剝除 markdown fence
            if raw.startswith("```"):
                raw = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()

            parsed = json.loads(raw)
            content = parsed.get("advance_organizer", "")
            if not content:
                log.warning("K-RE-01 LLM 回傳空 advance_organizer")
                return None
            return content

        except json.JSONDecodeError as e:
            log.warning("K-RE-01 LLM 回傳非合法 JSON: %s", e)
            return None
        except Exception as e:
            log.error("K-RE-01 LLM 呼叫失敗: %s", e)
            return None

    # ── DB 寫入 ──────────────────────────────────────────────────────────────

    def _persist_and_link(
        self,
        chapter: KnowledgeNode,
        content: str,
    ) -> Optional[dict]:
        """寫入 ResourceScaffold + 建 ScaffoldNodeLink.

        scaffold 掛 chapter 本身 + 所有後代節點（depth 1/2/3）。

        Args:
            chapter: 章節 KnowledgeNode（depth=1）
            content: advance_organizer 文字

        Returns:
            {"scaffold_id": str, "links_created": int} 或 None
        """
        try:
            scaffold = ResourceScaffold(
                resource_id=None,  # 純逆向工程，無教材資源
                type=ResourceScaffoldType.ADVANCE_ORGANIZER.value,
                content=content,
                chapter_heading=chapter.name,
                template_code=TEMPLATE_CODE,
                tenant_id=chapter.tenant_id,
                trust_level="SYSTEM_GENERATED",
                is_orphan_fill=False,
            )
            self.db.add(scaffold)
            self.db.flush()  # 取得 scaffold.id

            # 建 links：chapter 本身 + 所有後代節點
            descendant_nodes = self._get_all_descendant_nodes(chapter.id)
            all_nodes = [chapter] + descendant_nodes

            links_created = 0
            for node in all_nodes:
                # 防重複（若已有 unique constraint 衝突則跳過）
                existing_link = (
                    self.db.query(ScaffoldNodeLink)
                    .filter(
                        ScaffoldNodeLink.scaffold_id == scaffold.id,
                        ScaffoldNodeLink.node_id == node.id,
                    )
                    .first()
                )
                if existing_link:
                    continue
                link = ScaffoldNodeLink(
                    scaffold_id=scaffold.id,
                    node_id=node.id,
                    similarity=1.0,  # 章節直接對應
                    link_method="chapter_anchor",
                )
                self.db.add(link)
                links_created += 1

            self.db.commit()
            log.info(
                "K-RE-01 scaffold 寫入完成 chapter=%s scaffold_id=%s links=%d",
                chapter.name,
                scaffold.id,
                links_created,
            )
            return {"scaffold_id": str(scaffold.id), "links_created": links_created}

        except Exception as e:
            self.db.rollback()
            log.error("K-RE-01 _persist_and_link 失敗: %s", e)
            return None

    # ── Dry-run 工具 ─────────────────────────────────────────────────────────

    def estimate_cost(self, subject_id: str) -> dict:
        """估算對該 subject 跑 K-RE-01 的 token 成本（不打 LLM）.

        Args:
            subject_id: 科目 UUID 字串

        Returns:
            self.ok({
                "chapter_count": int,
                "chapters_to_generate": int,  # 扣除已有 K-RE-01 的章節
                "estimated_input_tokens": int,
                "estimated_output_tokens": int,
                "estimated_cost_usd": float,
                "sample_prompt": str,  # 第一個章節的 user_prompt 範例
            })
        """
        try:
            sid = uuid.UUID(subject_id)
        except ValueError:
            return self.error("無效的 subject_id 格式", 400)

        subject = self.db.query(Subject).filter(Subject.id == sid).first()
        if not subject:
            return self.error("科目不存在", 404)

        chapters = (
            self.db.query(KnowledgeNode)
            .filter(
                KnowledgeNode.subject_id == sid,
                KnowledgeNode.depth == 1,
            )
            .order_by(KnowledgeNode.sort_order, KnowledgeNode.created_at)
            .all()
        )

        to_generate = []
        for chapter in chapters:
            existing = (
                self.db.query(ResourceScaffold)
                .join(ScaffoldNodeLink, ScaffoldNodeLink.scaffold_id == ResourceScaffold.id)
                .filter(
                    ScaffoldNodeLink.node_id == chapter.id,
                    ResourceScaffold.type == ResourceScaffoldType.ADVANCE_ORGANIZER.value,
                    ResourceScaffold.template_code == TEMPLATE_CODE,
                )
                .first()
            )
            if not existing:
                stems = self._get_chapter_questions(chapter.id, subject)
                if stems:
                    to_generate.append(chapter)

        # 範例 prompt（第一個章節）
        sample_prompt = ""
        if to_generate:
            first = to_generate[0]
            child_names = self._get_child_node_names(first.id)
            stems = self._get_chapter_questions(first.id, subject)
            sample_prompt = _build_user_prompt(
                subject_name=subject.name,
                chapter_name=first.name,
                child_names=child_names,
                question_stems=stems,
            )

        count = len(to_generate)
        estimated_input = count * APPROX_INPUT_TOKENS_PER_CHAPTER
        estimated_output = count * APPROX_OUTPUT_TOKENS_PER_CHAPTER
        cost = (
            (estimated_input / 1000 * GEMINI_INPUT_PRICE_PER_1K)
            + (estimated_output / 1000 * GEMINI_OUTPUT_PRICE_PER_1K)
        )

        return self.ok({
            "subject_id": subject_id,
            "subject_name": subject.name,
            "chapter_count": len(chapters),
            "chapters_to_generate": count,
            "estimated_input_tokens": estimated_input,
            "estimated_output_tokens": estimated_output,
            "estimated_cost_usd": round(cost, 6),
            "sample_prompt": sample_prompt,
        })


# ── Module-level helpers ────────────────────────────────────────────────────

def _truncate_to_chars(text: str, max_chars: int) -> str:
    """截短到 max_chars 個字元（含標點）."""
    if len(text) <= max_chars:
        return text
    # 在 max_chars 處截斷，若末位是半句則退到最後一個句號
    truncated = text[:max_chars]
    for punct in ("。", "！", "？", "!", "?", ".", ";", "；"):
        last_idx = truncated.rfind(punct)
        if last_idx > max_chars // 2:
            return truncated[: last_idx + 1]
    return truncated


def _build_system_prompt() -> str:
    """建立 K-RE-01 system prompt."""
    return """\
你是一位精通 Ausubel Subsumption Theory 的教育設計師。你的任務是為「純逆向工程」的考試科目產生章節級讀前定錨（advance organizer）。

規則：
1. 80 字 hard limit（含標點，超過無效）
2. 必用日常情境類比，不寫學術定義
3. 禁止逐題講解，只給「這章關懷的方向」
4. 結尾必銜接「這章學：...」（說明本章核心學習方向）
5. 開頭擇一：「💡 你可能已經知道」「閱讀本章前，請想想：」「想想看：」「💡 想想：」
6. 禁止外部 URL
7. 輸出純 JSON：{"advance_organizer": "..."}"""


def _build_user_prompt(
    subject_name: str,
    chapter_name: str,
    child_names: list[str],
    question_stems: list[str],
) -> str:
    """建立 K-RE-01 user prompt."""
    child_lines = "\n".join(f"- {n}" for n in child_names) if child_names else "（無子節點）"
    stem_lines = "\n".join(f"{i+1}. {s}" for i, s in enumerate(question_stems)) if question_stems else "（無考古題）"
    return (
        f"科目：{subject_name}\n"
        f"章節：{chapter_name}\n"
        f"此章節底下節點：\n{child_lines}\n"
        f"此章節對應考古題（前 {len(question_stems)} 題 stem）：\n{stem_lines}\n\n"
        f"請產出 1 個 ≤80 字的 advance_organizer。輸出 JSON：\n"
        '{{"advance_organizer": "..."}}'
    )
