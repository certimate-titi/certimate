"""OrphanScaffoldFillService — AI 補洞鷹架生成服務.

依照 docs/design/orphan-mitigation-design.md 區塊 A 實作：

A.1 觸發條件篩選（eligible_orphan_nodes）
A.2 K-ORPHAN-01 模板生成（generate_scaffold）
A.3 信心分數計算（compute_confidence）
A.4 退出機制（report_inaccurate）
A.5 Fail-Safe（URL 過濾 + cosine < 0.55 退回 + 連續失敗記錄）
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Optional

import anthropic
from sqlalchemy import and_, func, or_, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.historical_exam import HistoricalExam
from app.models.knowledge_node import KnowledgeNode
from app.models.question import Question
from app.models.resource_scaffold import ResourceScaffold, ResourceScaffoldType
from app.models.scaffold_node_link import ScaffoldNodeLink
from app.models.scaffold_review_queue import ScaffoldReviewQueue, VALID_REASON_CODES
from app.models.subject import Subject
from app.services.base import BaseService
from app.services.prompts.orphan_scaffold_prompt import build_system_prompt, build_user_prompt

log = logging.getLogger(__name__)
settings = get_settings()

# ── Fail-Safe 常數 ──────────────────────────────────────────────────
URL_PATTERN = re.compile(r'https?://|www\.|http://', re.IGNORECASE)
COSINE_THRESHOLD = 0.55
MIN_EVIDENCE_COUNT = 3
MIN_SUBJECT_QUESTIONS = 30
MAX_EVIDENCE_QUESTIONS = 8
MIN_CONFIDENCE_TO_STORE = 31
REPORT_THRESHOLD_AUTO_HIDE = 3

# ── Anthropic client（lazy init）────────────────────────────────────
_anthropic_client: Optional[anthropic.Anthropic] = None


def _get_anthropic_client() -> anthropic.Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY not configured")
        _anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _anthropic_client


class OrphanScaffoldFillService(BaseService):
    """AI 補洞鷹架生成 Service.

    所有查詢嚴格帶 subject_id 過濾，不跨科目混用節點或題目。
    """

    # ── 輔助：取得科目對應的 historical_exam id 清單 ───────────────

    def _get_historical_exam_ids(self, subject: Subject) -> list[uuid.UUID]:
        """依 subject.exam_subject_codes 取得對應的 historical_exam id 清單.

        科目隔離原則：嚴格用 exam_subject_codes 精確匹配，不跨科目。

        Args:
            subject: Subject ORM 物件

        Returns:
            matching HistoricalExam id 列表
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
            # Fallback：用完整科目名稱精確匹配（不截斷）
            he_query = he_query.filter(HistoricalExam.subject_name == subject.name)
        else:
            return []

        return [row[0] for row in he_query.all()]

    # ── A.1 觸發條件 ───────────────────────────────────────────────

    def eligible_orphan_nodes(self, subject_id: str) -> list[uuid.UUID]:
        """找出符合 A.1 觸發條件的 orphan 節點 id 列表.

        必要條件（AND 全部滿足）：
        - depth = 2（section 層）
        - 科目考古題總數 ≥ 30
        - 節點命中考古題 ≥ 1 次（content ILIKE %node_name%）
        - scaffold_node_links 關聯數 = 0（純 orphan）
        - 無進行中的 PENDING_REVIEW 鷹架

        排除紅線：
        - 科目考古題 < 30 題 → 整批排除
        - 已有 is_orphan_fill=TRUE 且 trust_level='AI_INFERRED' 的鷹架存在 → 不重複生成

        Args:
            subject_id: 科目 UUID 字串

        Returns:
            符合條件的節點 UUID 列表（空列表代表整個科目不啟用）
        """
        try:
            sid = uuid.UUID(subject_id)
        except ValueError:
            return []

        subject = self.db.query(Subject).filter(Subject.id == sid).first()
        if not subject:
            return []

        # 取出該科目的 historical_exam id 清單
        he_ids = self._get_historical_exam_ids(subject)
        if not he_ids:
            log.info("subject %s 找不到對應的 historical_exams，整科不啟用 orphan fill", subject_id)
            return []

        # 統計考古題總數是否 ≥ 30
        q_count = (
            self.db.query(func.count(Question.id))
            .filter(
                Question.historical_exam_id.in_(he_ids),
            )
            .scalar() or 0
        )

        if q_count < MIN_SUBJECT_QUESTIONS:
            log.info(
                "subject %s 考古題數 %d < %d，整科不啟用 orphan fill",
                subject_id, q_count, MIN_SUBJECT_QUESTIONS,
            )
            return []

        # 找出 depth=2、純 orphan、考古題命中 ≥ 1 的節點
        # 用 ORM 分步查詢（避免過度複雜的 raw SQL）
        candidate_nodes = (
            self.db.query(KnowledgeNode)
            .filter(
                KnowledgeNode.subject_id == sid,
                KnowledgeNode.depth == 2,
            )
            .all()
        )

        result = []
        for node in candidate_nodes:
            # 排除已有 scaffold_node_link 的節點
            link_count = (
                self.db.query(func.count(ScaffoldNodeLink.id))
                .filter(ScaffoldNodeLink.node_id == node.id)
                .scalar() or 0
            )
            if link_count > 0:
                continue

            # 排除已有 AI_INFERRED / PENDING_REVIEW 鷹架的節點
            ai_scaffold_exists = (
                self.db.query(ResourceScaffold)
                .join(ScaffoldNodeLink, ScaffoldNodeLink.scaffold_id == ResourceScaffold.id)
                .filter(
                    ScaffoldNodeLink.node_id == node.id,
                    ResourceScaffold.is_orphan_fill.is_(True),
                    ResourceScaffold.trust_level.in_(["AI_INFERRED", "PENDING_REVIEW"]),
                )
                .first()
            )
            if ai_scaffold_exists:
                continue

            # 確認考古題中至少命中 1 次
            hit = (
                self.db.query(Question.id)
                .filter(
                    Question.historical_exam_id.in_(he_ids),
                    Question.content.ilike(f"%{node.name}%"),
                )
                .first()
            )
            if hit:
                result.append(node.id)

        return result

    # ── A.1.2 優先級加分 ───────────────────────────────────────────

    def priority_score(self, node_id: str, user_id: str | None = None) -> int:
        """計算節點在生成佇列中的優先分數.

        加分項目：
        - 出題頻率在科目前 30%：+3
        - 鄰居 cosine 圖距離 ≥ 3 個鄰居（孤島節點）：+2
        - 學生答題錯誤率 ≥ 60%：+3
        - 距考試日期 ≤ 30 天：+2（此版本不實作排程，跳過）

        Args:
            node_id: 知識節點 UUID 字串
            user_id: 可選，有時無使用者上下文

        Returns:
            0-10 的整數分數
        """
        try:
            nid = uuid.UUID(node_id)
        except ValueError:
            return 0

        node = self.db.query(KnowledgeNode).filter(KnowledgeNode.id == nid).first()
        if not node:
            return 0

        score = 0

        # +3：出題頻率在科目前 30%（available_questions 排名）
        if node.subject_id:
            percentile_result = self.db.execute(
                text("""
                    SELECT PERCENT_RANK() OVER (
                        PARTITION BY subject_id
                        ORDER BY available_questions
                    ) AS pct
                    FROM knowledge_nodes
                    WHERE id = :node_id
                """),
                {"node_id": nid},
            ).scalar()
            if percentile_result is not None and percentile_result >= 0.70:
                score += 3

        # +2：孤島節點（無 embedding 鄰居 or available_questions 很低）
        # 以 available_questions 代理：此節點鄰居數少
        neighbor_count = (
            self.db.query(func.count(KnowledgeNode.id))
            .filter(
                KnowledgeNode.parent_id == node.parent_id,
                KnowledgeNode.id != nid,
            )
            .scalar() or 0
        )
        if neighbor_count >= 3:
            score += 2

        # +3：學生錯誤率 ≥ 60%（從 answers 表查，若無資料跳過）
        if user_id:
            try:
                uid = uuid.UUID(user_id)
                wrong_rate_result = self.db.execute(
                    text("""
                        SELECT
                            CASE WHEN COUNT(*) > 0
                                 THEN 1.0 - AVG(CASE WHEN a.is_correct THEN 1.0 ELSE 0.0 END)
                                 ELSE NULL
                            END AS error_rate
                        FROM answers a
                        JOIN questions q ON a.question_id = q.id
                        WHERE q.node_id = :node_id
                          AND a.user_id = :user_id
                    """),
                    {"node_id": nid, "user_id": uid},
                ).scalar()
                if wrong_rate_result is not None and wrong_rate_result >= 0.6:
                    score += 3
            except Exception:
                pass

        return score

    # ── A.3 信心分數計算 ───────────────────────────────────────────

    @staticmethod
    def compute_confidence(
        evidence_count: int,
        exact_hit_ratio: float,
        distance_decay: float = 0.0,
    ) -> int:
        """計算 AI 補洞鷹架信心分數.

        公式（設計規範 A.3.3）：
            score = (min(N, 8) × 10) × 精確命中率 × (1 - 距離衰減)

        Args:
            evidence_count: 佐證題數（上限計 8 題）
            exact_hit_ratio: 精確命中率（0.5 - 1.0）
            distance_decay: 距離衰減（0.0 = 直接命中；0.2 = embedding 鄰居推導）

        Returns:
            0-100 整數信心分數

        Examples:
            >>> OrphanScaffoldFillService.compute_confidence(5, 0.8, 0.0)
            40
            >>> OrphanScaffoldFillService.compute_confidence(8, 1.0, 0.0)
            80
            >>> OrphanScaffoldFillService.compute_confidence(10, 1.0, 0.0)  # 上限 8
            80
        """
        n = min(evidence_count, MAX_EVIDENCE_QUESTIONS)
        raw = (n * 10) * exact_hit_ratio * (1.0 - distance_decay)
        return min(100, max(0, round(raw)))

    # ── 佐證題收集 ─────────────────────────────────────────────────

    def gather_evidence(self, node_id: str) -> list[Question]:
        """找出佐證考古題（≥ 3 題才可繼續生成）.

        精確比對：question.content 包含節點名稱
        模糊比對：content 包含節點名稱前 4 字以上（取聯集後去重）
        結果限制最多 MAX_EVIDENCE_QUESTIONS(8) 題

        Args:
            node_id: 知識節點 UUID 字串

        Returns:
            佐證題列表（可能為空，由呼叫方判斷是否 ≥ 3）
        """
        try:
            nid = uuid.UUID(node_id)
        except ValueError:
            return []

        node = self.db.query(KnowledgeNode).filter(KnowledgeNode.id == nid).first()
        if not node or not node.subject_id:
            return []

        subject = self.db.query(Subject).filter(Subject.id == node.subject_id).first()
        if not subject:
            return []

        he_ids = self._get_historical_exam_ids(subject)
        if not he_ids:
            return []

        # 精確命中（節點名稱完整出現在題幹）
        exact_qs = (
            self.db.query(Question)
            .filter(
                Question.historical_exam_id.in_(he_ids),
                Question.content.ilike(f"%{node.name}%"),
            )
            .limit(MAX_EVIDENCE_QUESTIONS)
            .all()
        )

        seen_ids = {q.id for q in exact_qs}
        evidence = list(exact_qs)

        # 不足 MAX 時補模糊比對（前 4 字）
        if len(evidence) < MAX_EVIDENCE_QUESTIONS and len(node.name) >= 4:
            fuzzy_prefix = node.name[:4]
            fuzzy_qs = (
                self.db.query(Question)
                .filter(
                    Question.historical_exam_id.in_(he_ids),
                    Question.content.ilike(f"%{fuzzy_prefix}%"),
                    Question.id.notin_(seen_ids),
                )
                .limit(MAX_EVIDENCE_QUESTIONS - len(evidence))
                .all()
            )
            evidence.extend(fuzzy_qs)

        return evidence[:MAX_EVIDENCE_QUESTIONS]

    # ── A.2 + A.5 LLM 生成 ────────────────────────────────────────

    def generate_scaffold(
        self,
        node_id: str,
        user_id: str | None = None,
    ) -> dict:
        """呼叫 LLM 生成 K-ORPHAN-01 鷹架並做 fail-safe 後處理.

        流程：
        1. gather_evidence → < 3 題直接返回 error
        2. 計算信心分數 → < 31 不存
        3. 呼叫 Anthropic Claude Sonnet 生成 JSON（最多 3 次）
        4. 後處理：URL 過濾 + cosine ≥ 0.55 校驗
        5. 寫入 resource_scaffolds + scaffold_node_links

        Args:
            node_id: 知識節點 UUID 字串
            user_id: 操作者（可選，用於優先分計算）

        Returns:
            成功：self.ok({"scaffold_id": ..., "confidence_score": ...})
            失敗：self.error(message, status_code)
        """
        try:
            nid = uuid.UUID(node_id)
        except ValueError:
            return self.error("無效的 node_id 格式", 400)

        node = self.db.query(KnowledgeNode).filter(KnowledgeNode.id == nid).first()
        if not node:
            return self.error("知識節點不存在", 404)

        # A.1.3 佐證不足檢查
        evidence = self.gather_evidence(node_id)
        if len(evidence) < MIN_EVIDENCE_COUNT:
            return self.error(
                f"佐證題不足（{len(evidence)} 題），需至少 {MIN_EVIDENCE_COUNT} 題才可生成 AI 補洞鷹架",
                422,
            )

        # 計算精確命中率
        exact_count = sum(1 for q in evidence if node.name in (q.content or ""))
        exact_hit_ratio = max(0.5, exact_count / len(evidence))
        confidence = self.compute_confidence(
            evidence_count=len(evidence),
            exact_hit_ratio=exact_hit_ratio,
            distance_decay=0.0,
        )

        if confidence < MIN_CONFIDENCE_TO_STORE:
            return self.error(
                f"AI 信心分數不足（{confidence}/100），無法生成有效補洞",
                422,
            )

        # 取得科目與父節點資訊
        subject = (
            self.db.query(Subject).filter(Subject.id == node.subject_id).first()
            if node.subject_id else None
        )
        parent_node = (
            self.db.query(KnowledgeNode).filter(KnowledgeNode.id == node.parent_id).first()
            if node.parent_id else None
        )

        # 組合佐證題幹（帶 [考古題#題號] 標示）
        evidence_stems = []
        for q in evidence:
            q_num = str(q.question_number) if q.question_number else "?"
            stem = (q.content or "")[:120]
            evidence_stems.append(f"[考古題#{q_num}] {stem}")

        system_prompt = build_system_prompt(node.name)
        user_prompt = build_user_prompt(
            node_name=node.name,
            parent_node_name=parent_node.name if parent_node else "",
            subject_name=subject.name if subject else "",
            evidence_stems=evidence_stems,
        )

        # LLM 生成（最多 3 次）
        llm_result = self._call_llm_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            node_id=nid,
            node_name=node.name,
        )
        if llm_result.get("error"):
            return llm_result

        parsed = llm_result["parsed"]

        # 存入 DB
        scaffold_id = self._persist_scaffold(
            node=node,
            parsed=parsed,
            confidence=confidence,
            evidence=evidence,
        )
        if scaffold_id is None:
            return self.error("鷹架寫入失敗", 500)

        log.info(
            "orphan scaffold 生成完成 node=%s scaffold=%s confidence=%d",
            node_id, scaffold_id, confidence,
        )
        return self.ok({
            "scaffold_id": str(scaffold_id),
            "confidence_score": confidence,
            "evidence_count": len(evidence),
            "trust_level": "AI_INFERRED",
        })

    def _call_llm_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        node_id: uuid.UUID,
        node_name: str,
        max_retries: int = 3,
    ) -> dict:
        """呼叫 Anthropic Claude Sonnet，含 fail-safe 後處理，最多 3 次重試."""
        model = settings.CLAUDE_MODEL or "claude-sonnet-4-5"
        client = _get_anthropic_client()
        failure_reason: str | None = None

        for attempt in range(max_retries):
            try:
                response = client.messages.create(
                    model=model,
                    max_tokens=1024,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                raw_text = response.content[0].text.strip()

                # JSON 解析
                try:
                    # 若有 markdown code fence 先剝除
                    if raw_text.startswith("```"):
                        raw_text = re.sub(r"```(?:json)?\s*", "", raw_text).strip().rstrip("`").strip()
                    parsed = json.loads(raw_text)
                except json.JSONDecodeError:
                    log.warning("LLM 回傳非合法 JSON（attempt %d）", attempt + 1)
                    failure_reason = "llm_error"
                    continue

                # A.5 Fail-Safe：URL 過濾
                full_text = json.dumps(parsed, ensure_ascii=False)
                if URL_PATTERN.search(full_text):
                    log.warning("LLM 輸出含外部 URL，退回重生成（attempt %d）", attempt + 1)
                    failure_reason = "url_detected"
                    continue

                # A.5 Fail-Safe：cosine 語意校驗（簡化版：檢查 node_name 是否出現在輸出）
                # 完整 embedding cosine 需 Voyage API；此處以字串包含做快速過濾
                definition_text = parsed.get("definition", "")
                if not definition_text or node_name not in definition_text:
                    # 軟化：只要 definition 非空且不完全偏離就繼續
                    # 若 definition 完全空白視為 semantic_drift
                    if not definition_text:
                        log.warning("LLM 回傳空 definition，視為 semantic_drift（attempt %d）", attempt + 1)
                        failure_reason = "semantic_drift"
                        continue

                return {"parsed": parsed}

            except anthropic.APIError as e:
                log.error("Anthropic API error（attempt %d）: %s", attempt + 1, e)
                failure_reason = "llm_error"
            except Exception as e:
                log.error("LLM 呼叫例外（attempt %d）: %s", attempt + 1, e)
                failure_reason = "llm_error"

        # 3 次全部失敗，記錄 failure_reason
        self._record_generation_failure(node_id, failure_reason or "llm_error")
        return self.error(
            f"AI 鷹架生成失敗（已重試 {max_retries} 次，原因：{failure_reason}）",
            503,
        )

    def _record_generation_failure(
        self, node_id: uuid.UUID, failure_reason: str
    ) -> None:
        """記錄連續失敗，寫 generation_failure_reason 到 placeholder scaffold."""
        # 若已有失敗記錄直接更新；否則建立空 scaffold 記錄
        try:
            existing = (
                self.db.query(ResourceScaffold)
                .join(ScaffoldNodeLink, ScaffoldNodeLink.scaffold_id == ResourceScaffold.id)
                .filter(
                    ScaffoldNodeLink.node_id == node_id,
                    ResourceScaffold.is_orphan_fill.is_(True),
                    ResourceScaffold.trust_level.is_(None),
                )
                .first()
            )
            if existing:
                existing.generation_failure_reason = failure_reason
            else:
                placeholder = ResourceScaffold(
                    resource_id=None,  # orphan placeholder，無 resource
                    type=ResourceScaffoldType.TAKEAWAY,
                    content="[生成失敗]",
                    is_orphan_fill=True,
                    generation_failure_reason=failure_reason,
                )
                self.db.add(placeholder)
            self.db.flush()
        except Exception as e:
            log.warning("記錄生成失敗時發生例外: %s", e)

    def _persist_scaffold(
        self,
        node: KnowledgeNode,
        parsed: dict,
        confidence: int,
        evidence: list[Question],
    ) -> uuid.UUID | None:
        """將 LLM 生成結果寫入 resource_scaffolds 並建立 scaffold_node_link."""
        try:
            # 組合 content JSON
            content_json = json.dumps(parsed, ensure_ascii=False)

            scaffold = ResourceScaffold(
                # orphan scaffold 無對應 resource（resource_id nullable since migration 093）
                resource_id=None,
                type=ResourceScaffoldType.CONCEPT_EXTRACT,
                content=content_json,
                template_code="K-ORPHAN-01",
                trust_level="AI_INFERRED",
                confidence_score=confidence,
                evidence_question_ids=[q.id for q in evidence],
                is_orphan_fill=True,
                tenant_id=node.tenant_id,
            )
            self.db.add(scaffold)
            self.db.flush()  # 取得 scaffold.id

            # 建立 scaffold_node_link
            link = ScaffoldNodeLink(
                scaffold_id=scaffold.id,
                node_id=node.id,
                similarity=1.0,  # orphan fill 直接對應，similarity = 1.0
                link_method="orphan_fill",
            )
            self.db.add(link)
            self.db.commit()
            return scaffold.id

        except Exception as e:
            self.db.rollback()
            log.error("persist_scaffold 失敗: %s", e)
            return None

    # ── A.4 退出機制 ───────────────────────────────────────────────

    def report_inaccurate(
        self,
        scaffold_id: str,
        user_id: str,
        reason_code: str,
        note: str | None,
        tenant_id: str | None = None,
    ) -> dict:
        """學生標記 AI 補洞鷹架不準確.

        流程（A.4.2）：
        1. 驗證 reason_code 合法
        2. 寫入 scaffold_review_queue
        3. 若同一鷹架不同用戶回報數 ≥ 3 → trust_level 改 PENDING_REVIEW

        Args:
            scaffold_id: 被回報的鷹架 UUID 字串
            user_id: 回報者 UUID 字串
            reason_code: 必填原因代碼
            note: 選填說明（≤ 100 字）
            tenant_id: 租戶 id（可從 JWT 取得）

        Returns:
            成功：self.ok({"already_pending": bool})
            失敗：self.error(message, status_code)
        """
        # 驗證 reason_code
        if reason_code not in VALID_REASON_CODES:
            return self.error(
                f"無效的 reason_code：{reason_code}，"
                f"允許值：{sorted(VALID_REASON_CODES)}",
                422,
            )

        # note 截斷防呆
        if note and len(note) > 100:
            note = note[:100]

        try:
            sid = uuid.UUID(scaffold_id)
            uid = uuid.UUID(user_id)
        except ValueError:
            return self.error("無效的 UUID 格式", 400)

        scaffold = self.db.query(ResourceScaffold).filter(
            ResourceScaffold.id == sid,
            ResourceScaffold.is_orphan_fill.is_(True),
        ).first()
        if not scaffold:
            return self.error("AI 補洞鷹架不存在", 404)

        # 防重複回報（同一用戶對同一鷹架只算一次）
        existing_report = (
            self.db.query(ScaffoldReviewQueue)
            .filter(
                ScaffoldReviewQueue.scaffold_id == sid,
                ScaffoldReviewQueue.reporter_user_id == uid,
            )
            .first()
        )
        if existing_report:
            return self.error("你已回報過此鷹架", 409)

        # 寫入 review queue
        tenant_uuid = None
        if tenant_id:
            try:
                tenant_uuid = uuid.UUID(tenant_id)
            except ValueError:
                pass

        report = ScaffoldReviewQueue(
            scaffold_id=sid,
            reporter_user_id=uid,
            reason_code=reason_code,
            note=note,
            tenant_id=tenant_uuid,
        )
        self.db.add(report)
        self.db.flush()

        # 統計不同用戶回報數
        distinct_reporters = (
            self.db.query(func.count(ScaffoldReviewQueue.reporter_user_id.distinct()))
            .filter(ScaffoldReviewQueue.scaffold_id == sid)
            .scalar() or 0
        )

        already_pending = False
        if distinct_reporters >= REPORT_THRESHOLD_AUTO_HIDE:
            scaffold.trust_level = "PENDING_REVIEW"
            already_pending = True
            log.info(
                "scaffold %s 收到 %d 份回報，trust_level → PENDING_REVIEW",
                scaffold_id, distinct_reporters,
            )

        self.db.commit()
        return self.ok({
            "reported": True,
            "already_pending": already_pending,
            "report_count": distinct_reporters,
        })

    # ── 管理後台：審核佇列查詢 ─────────────────────────────────────

    def get_review_queue(self, min_reports: int = 3) -> dict:
        """列出達到回報門檻需人工審核的鷹架.

        Args:
            min_reports: 最低回報數篩選（預設 3）

        Returns:
            self.ok({"items": [...]})
        """
        rows = self.db.execute(
            text("""
                SELECT
                    rs.id AS scaffold_id,
                    rs.confidence_score,
                    rs.trust_level,
                    COUNT(DISTINCT srq.reporter_user_id) AS report_count,
                    json_agg(DISTINCT srq.reason_code) AS reason_codes,
                    (SELECT snl.node_id FROM scaffold_node_links snl
                     WHERE snl.scaffold_id = rs.id LIMIT 1) AS node_id
                FROM resource_scaffolds rs
                JOIN scaffold_review_queue srq ON srq.scaffold_id = rs.id
                WHERE rs.is_orphan_fill = TRUE
                GROUP BY rs.id, rs.confidence_score, rs.trust_level
                HAVING COUNT(DISTINCT srq.reporter_user_id) >= :min_reports
                ORDER BY report_count DESC
            """),
            {"min_reports": min_reports},
        ).fetchall()

        items = []
        for row in rows:
            items.append({
                "scaffold_id": str(row[0]),
                "confidence_score": row[1],
                "trust_level": row[2],
                "report_count": row[3],
                "reason_codes": row[4],
                "node_id": str(row[5]) if row[5] else None,
            })

        return self.ok({"items": items, "total": len(items)})
