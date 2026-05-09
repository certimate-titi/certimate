"""OrphanCoachService — AI 蘇格拉底教練對話服務.

#9 AI 教練回應 Orphan 節點（蘇格拉底對話）。
對應 docs/design/orphan-mitigation-design.md 區塊 C。

設計要點：
  - C.1 蘇格拉底式提問（不給答案，只引導）
  - C.2 Context 注入：node + neighbor_nodes(top-3 cosine) + exam_frequency + student_mastery
  - C.3 評分：概念接觸度(LLM) + 推理連結度(LLM) + 主動性(規則：≥20字非隨機)
  - C.3.2 mastery 降權：對話得分/2.5 × 0.4，E-Factor=1.8
  - C.4 結束條件：5輪零接觸→轉介、3輪≥1.0→插考古題、8輪強制、3分鐘暫停可續
  - C.6 LLM 選擇：FREE/PRO=Haiku 3.5，PRO+/ULTRA=Sonnet 4.5
  - 配額：FREE 月 5 次，PRO 月 20 次，PRO+/ULTRA 無限
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import anthropic
from sqlalchemy import and_, func, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.ai_chat import AiChatMessage, AiChatSession
from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery
from app.models.subject import Subject
from app.models.user import User, SubscriptionPlan
from app.models.user_usage import UserUsage
from app.services.base import BaseService
from app.services.prompts.orphan_coach_prompts import (
    SYSTEM_PROMPT_SOCRATIC,
    build_closing_force_end,
    build_closing_positive,
    build_closing_switch_question,
    build_closing_transfer_book,
    build_evaluator_prompt,
)

log = logging.getLogger("certimate.orphan_coach")
settings = get_settings()

# ── 常數 ──────────────────────────────────────────────────────────
SOCRATIC_MODE = "socratic_orphan"
MAX_ROUNDS = 8
FORCE_END_ROUNDS = 8
TRANSFER_BOOK_ZERO_ROUNDS = 5   # 5 輪後仍零概念接觸 → 轉介書籍
SWITCH_QUESTION_MIN_ROUNDS = 3  # ≥ 3 輪且得分 ≥ 1.0 → 插入考古題
SWITCH_QUESTION_MIN_SCORE = 1.0
POSITIVE_CLOSE_MIN_SCORE = 1.5  # ≥ 1.5/2.5 視為正向收尾
MASTERY_COMMIT_MIN_ROUNDS = 3   # 至少 3 輪
MASTERY_COMMIT_MIN_HIGH_ROUNDS = 2  # 至少 2 輪 ≥ 1.5/2.5
MASTERY_DISCOUNT = 0.4          # 對話 mastery 降權係數
EFACTOR_SOCRATIC = 1.8          # SM-2 E-Factor（低於正式答題的 2.5）
PAUSE_TIMEOUT_SECONDS = 180     # 3 分鐘無回應暫停
INITIATIVE_MIN_CHARS = 20       # 主動性規則：≥ 20 字
# 配額（月次數）
QUOTA_FREE = 5
QUOTA_PRO = 20
QUOTA_PRO_PLUS = -1  # 無限
QUOTA_ULTRA = -1     # 無限

# Haiku = FREE/PRO；Sonnet = PRO+/ULTRA
MODEL_HAIKU = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"

# 隨機輸入偵測：僅含標點 / 重複字符
_RANDOM_INPUT_RE = re.compile(r'^[^\w一-鿿]*$|^(.)\1{4,}$')

# ── Anthropic client（lazy init）────────────────────────────────────
_anthropic_client: Optional[anthropic.Anthropic] = None


def _get_anthropic() -> anthropic.Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _anthropic_client


class OrphanCoachService(BaseService):
    """AI 蘇格拉底教練對話服務。"""

    # ── 公開 API ──────────────────────────────────────────────────

    def start_conversation(self, user_id: str, node_id: str) -> dict:
        """建立新對話 session，產生 LLM 第一句引導問句。

        Returns:
            ok dict with: conversation_id, opening_message, context_summary
        Error:
            404 節點不存在
            402 配額不足
            400 對話已存在且進行中
        """
        user_uuid = self._parse_uuid(user_id)
        if isinstance(user_uuid, dict):
            return user_uuid
        node_uuid = self._parse_uuid(node_id)
        if isinstance(node_uuid, dict):
            return node_uuid

        # 驗證節點存在
        node = self.db.query(KnowledgeNode).filter(KnowledgeNode.id == node_uuid).first()
        if not node:
            return self.error("知識節點不存在", 404)

        # 配額檢查
        quota_check = self._check_quota(user_uuid)
        if isinstance(quota_check, dict) and quota_check.get("error"):
            return quota_check

        # 建 Session
        model = self._select_llm(user_uuid)
        session = AiChatSession(
            user_id=user_uuid,
            context_type="knowledge_node",
            context_id=node_uuid,
            model_used=model,
            mode=SOCRATIC_MODE,
            node_id=node_uuid,
            message_count=0,
            mastery_committed=False,
        )
        self.db.add(session)
        self.db.flush()

        # 組 context + 呼叫 LLM
        context = self._build_context(node_uuid, user_uuid)
        opening_message = self._call_llm_opening(model, context)

        # 寫 assistant 第一則訊息
        msg = AiChatMessage(
            session_id=session.id,
            role="assistant",
            content=opening_message,
            token_count=None,
        )
        self.db.add(msg)
        session.message_count = 1
        self.db.commit()

        # 更新配額使用量
        self._increment_quota(user_uuid)

        context_summary = self._build_context_summary(context)
        return self.ok({
            "conversation_id": str(session.id),
            "opening_message": opening_message,
            "context_summary": context_summary,
        })

    def send_message(self, conversation_id: str, user_text: str, user_id: str) -> dict:
        """接收學生回覆，評分後讓 LLM 繼續引導，並判斷是否結束對話。

        Returns:
            ok dict with: assistant_reply, scores, round_number, status
        Error:
            404 對話不存在
            403 非本人對話
            410 對話已結束（message_count >= MAX_ROUNDS*2）
        """
        session_uuid = self._parse_uuid(conversation_id)
        if isinstance(session_uuid, dict):
            return session_uuid
        user_uuid = self._parse_uuid(user_id)
        if isinstance(user_uuid, dict):
            return user_uuid

        session = self.db.query(AiChatSession).filter(
            AiChatSession.id == session_uuid,
            AiChatSession.mode == SOCRATIC_MODE,
        ).first()
        if not session:
            return self.error("對話不存在", 404)
        if str(session.user_id) != str(user_uuid):
            return self.error("無存取權限", 403)

        # 計算目前輪數（user 訊息數 = 問答輪次數）
        all_messages = self.db.query(AiChatMessage).filter(
            AiChatMessage.session_id == session_uuid
        ).order_by(AiChatMessage.created_at).all()

        user_messages = [m for m in all_messages if m.role == "user"]
        current_round = len(user_messages) + 1  # 本次為第 current_round 輪

        if current_round > MAX_ROUNDS:
            return self.error("對話已超過上限，請開始新對話", 410)

        # 取最後一則 assistant 問句（用於評分 context）
        assistant_messages = [m for m in all_messages if m.role == "assistant"]
        last_ai_question = assistant_messages[-1].content if assistant_messages else ""

        # 評分
        scores = self._evaluate_turn(user_text, last_ai_question)

        # 寫 user message
        user_msg = AiChatMessage(
            session_id=session_uuid,
            role="user",
            content=user_text,
            score_concept=scores["concept"],
            score_reasoning=scores["reasoning"],
            score_initiative=scores["initiative"],
            round_score=scores["total"],
        )
        self.db.add(user_msg)

        # 更新 session 最新評分
        session.score_concept = scores["concept"]
        session.score_reasoning = scores["reasoning"]
        session.score_initiative = scores["initiative"]
        session.final_score = scores["total"]
        session.message_count += 1
        session.paused_at = None  # 學生回覆，清除暫停狀態

        # 判斷結束條件
        all_user_msgs_scores = [
            {"round_score": m.round_score or 0.0} for m in user_messages
        ] + [{"round_score": scores["total"]}]

        end_check = self._check_end_conditions(
            round_number=current_round,
            all_scores=all_user_msgs_scores,
            node=self.db.query(KnowledgeNode).filter(
                KnowledgeNode.id == session.node_id
            ).first(),
        )

        if end_check["should_end"]:
            status = end_check["reason"]
            assistant_reply = self._build_closing_reply(
                reason=status,
                node=self.db.query(KnowledgeNode).filter(
                    KnowledgeNode.id == session.node_id
                ).first(),
                scores=all_user_msgs_scores,
            )
        else:
            status = "continuing"
            # LLM 繼續引導
            context = self._build_context(session.node_id, user_uuid)
            conversation_history = self._build_conversation_history(all_messages, user_text)
            assistant_reply = self._call_llm_continue(
                session.model_used or MODEL_HAIKU,
                context,
                conversation_history,
                scores,
            )

        # 寫 assistant 回覆
        ai_msg = AiChatMessage(
            session_id=session_uuid,
            role="assistant",
            content=assistant_reply,
        )
        self.db.add(ai_msg)
        session.message_count += 1

        # 若結束，檢查是否需要 commit mastery
        if end_check["should_end"] and end_check["reason"] in (
            "positive_close", "switch_to_question"
        ):
            self._commit_mastery_if_eligible(session, all_user_msgs_scores)

        self.db.commit()

        return self.ok({
            "assistant_reply": assistant_reply,
            "scores": {
                "concept": scores["concept"],
                "reasoning": scores["reasoning"],
                "initiative": scores["initiative"],
                "total": scores["total"],
            },
            "round_number": current_round,
            "status": status,
        })

    def get_conversation(self, conversation_id: str, user_id: str) -> dict:
        """取得對話詳情（訊息清單、評分、mastery_committed、status）。"""
        session_uuid = self._parse_uuid(conversation_id)
        if isinstance(session_uuid, dict):
            return session_uuid
        user_uuid = self._parse_uuid(user_id)
        if isinstance(user_uuid, dict):
            return user_uuid

        session = self.db.query(AiChatSession).filter(
            AiChatSession.id == session_uuid,
            AiChatSession.mode == SOCRATIC_MODE,
        ).first()
        if not session:
            return self.error("對話不存在", 404)
        if str(session.user_id) != str(user_uuid):
            return self.error("無存取權限", 403)

        messages = self.db.query(AiChatMessage).filter(
            AiChatMessage.session_id == session_uuid
        ).order_by(AiChatMessage.created_at).all()

        user_msgs = [m for m in messages if m.role == "user"]
        total_score = sum(m.round_score or 0.0 for m in user_msgs)

        status = self._derive_status(session, len(user_msgs), user_msgs)

        return self.ok({
            "conversation_id": str(session.id),
            "node_id": str(session.node_id) if session.node_id else None,
            "messages": [
                {
                    "id": str(m.id),
                    "role": m.role,
                    "content": m.content,
                    "scores": {
                        "concept": m.score_concept,
                        "reasoning": m.score_reasoning,
                        "initiative": m.score_initiative,
                        "total": m.round_score,
                    } if m.role == "user" else None,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in messages
            ],
            "total_score": total_score,
            "mastery_committed": session.mastery_committed,
            "status": status,
            "paused_at": session.paused_at.isoformat() if session.paused_at else None,
        })

    def find_active_conversation(self, user_id: str, node_id: str) -> dict:
        """查找該使用者對同一節點的暫停/進行中對話（C.4.4 接續用）。

        Returns:
            ok dict with: existing_conversation_id (str | None)
        """
        user_uuid = self._parse_uuid(user_id)
        if isinstance(user_uuid, dict):
            return user_uuid
        node_uuid = self._parse_uuid(node_id)
        if isinstance(node_uuid, dict):
            return node_uuid

        # 查有效的（未超過上限、未 mastery_committed）暫停對話
        session = self.db.query(AiChatSession).filter(
            AiChatSession.user_id == user_uuid,
            AiChatSession.node_id == node_uuid,
            AiChatSession.mode == SOCRATIC_MODE,
            AiChatSession.mastery_committed == False,  # noqa: E712
            AiChatSession.message_count < MAX_ROUNDS * 2,
        ).order_by(AiChatSession.created_at.desc()).first()

        return self.ok({
            "existing_conversation_id": str(session.id) if session else None,
        })

    def pause_conversation(self, conversation_id: str, user_id: str) -> dict:
        """標記對話為暫停（設置 paused_at 時間戳）。"""
        session_uuid = self._parse_uuid(conversation_id)
        if isinstance(session_uuid, dict):
            return session_uuid
        user_uuid = self._parse_uuid(user_id)
        if isinstance(user_uuid, dict):
            return user_uuid

        session = self.db.query(AiChatSession).filter(
            AiChatSession.id == session_uuid,
            AiChatSession.mode == SOCRATIC_MODE,
        ).first()
        if not session:
            return self.error("對話不存在", 404)
        if str(session.user_id) != str(user_uuid):
            return self.error("無存取權限", 403)

        session.paused_at = datetime.now(timezone.utc)
        self.db.commit()
        return self.ok({"paused": True})

    # ── 內部輔助 ──────────────────────────────────────────────────

    def _parse_uuid(self, value: str) -> uuid.UUID | dict:
        """解析 UUID 字串，失敗回傳 error dict。"""
        try:
            return uuid.UUID(str(value))
        except (ValueError, AttributeError):
            return self.error(f"無效 UUID 格式: {value}", 400)

    def _select_llm(self, user_id: uuid.UUID) -> str:
        """C.6.2 依訂閱方案選 LLM。

        FREE / PRO → Haiku 3.5
        PRO_PLUS / ULTRA → Sonnet 4.5
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return MODEL_HAIKU
        plan = user.subscription_plan
        if plan in (SubscriptionPlan.PRO_PLUS, SubscriptionPlan.ULTRA):
            return MODEL_SONNET
        return MODEL_HAIKU

    def _check_quota(self, user_id: uuid.UUID) -> dict | None:
        """檢查月配額（FREE=5次，PRO=20次，PRO+/ULTRA=無限）。"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return self.error("使用者不存在", 404)

        plan = user.subscription_plan
        if plan in (SubscriptionPlan.PRO_PLUS, SubscriptionPlan.ULTRA):
            return None  # 無限

        period = datetime.now(timezone.utc).strftime("%Y-%m")
        usage = self.db.query(UserUsage).filter(
            UserUsage.user_id == user_id,
            UserUsage.period == period,
        ).first()

        monthly_orphan_used = getattr(usage, "monthly_orphan_coach_used", 0) if usage else 0
        quota = QUOTA_FREE if plan == SubscriptionPlan.FREE else QUOTA_PRO

        if monthly_orphan_used >= quota:
            return self.error(
                f"本月 AI 蘇格拉底教練次數已達上限（{quota} 次），請升級訂閱方案",
                402,
            )
        return None

    def _increment_quota(self, user_id: uuid.UUID) -> None:
        """增加月使用量（直接對 daily_ai_chats_used 計數，重用既有 UserUsage 表）。"""
        period = datetime.now(timezone.utc).strftime("%Y-%m")
        usage = self.db.query(UserUsage).filter(
            UserUsage.user_id == user_id,
            UserUsage.period == period,
        ).first()
        if usage:
            usage.daily_ai_chats_used = (usage.daily_ai_chats_used or 0) + 1
        else:
            usage = UserUsage(
                user_id=user_id,
                period=period,
                daily_ai_chats_used=1,
            )
            self.db.add(usage)
        # 不 commit，由呼叫方統一 commit

    def _build_context(self, node_id: uuid.UUID, user_id: uuid.UUID) -> dict:
        """C.2 組裝 LLM Context 注入物件。"""
        node = self.db.query(KnowledgeNode).filter(KnowledgeNode.id == node_id).first()
        if not node:
            return {}

        # 父節點名稱
        parent_name = None
        if node.parent_id:
            parent = self.db.query(KnowledgeNode).filter(
                KnowledgeNode.id == node.parent_id
            ).first()
            parent_name = parent.name if parent else None

        # 科目名稱
        subject_name = None
        if node.subject_id:
            subject = self.db.query(Subject).filter(
                Subject.id == node.subject_id
            ).first()
            subject_name = subject.name if subject else None

        # 鄰居節點 top-3（cosine similarity，同科目過濾）
        neighbor_nodes = self._get_neighbor_nodes(node, user_id)

        # 出題頻率
        total_in_subject = self._count_subject_questions(node.subject_id)
        questions_hitting = node.available_questions or 0
        frequency_percentile = self._compute_frequency_percentile(
            node_id, node.subject_id
        )

        # 學生 mastery
        mastery_record = self.db.query(NodeMastery).filter(
            NodeMastery.user_id == user_id,
            NodeMastery.node_id == node_id,
        ).first()
        mastery_score = mastery_record.base_mastery if mastery_record else 0.0
        last_attempted_at = (
            mastery_record.last_tested_at.isoformat()
            if mastery_record and mastery_record.last_tested_at
            else None
        )

        # days_to_exam（從 User 的 exam_date 計算，若無則 None）
        user = self.db.query(User).filter(User.id == user_id).first()
        days_to_exam = None
        if user and hasattr(user, "exam_date") and user.exam_date:
            delta = user.exam_date - datetime.now(timezone.utc).date()
            days_to_exam = delta.days

        return {
            "trigger_type": "orphan_node",
            "node": {
                "id": str(node_id),
                "name": node.name[:50],  # token 成本控制：截斷 50 字
                "depth": node.depth,
                "parent_name": parent_name,
                "subject_name": subject_name,
            },
            "neighbor_nodes": neighbor_nodes,
            "exam_frequency": {
                "total_questions_in_subject": total_in_subject,
                "questions_hitting_this_node": questions_hitting,
                "frequency_percentile": frequency_percentile,
            },
            "student_context": {
                "mastery_score": mastery_score,
                "last_attempted_at": last_attempted_at,
                "days_to_exam": days_to_exam,
                "subscription_tier": user.subscription_plan.value if user else "FREE",
            },
            "ai_scaffold_available": False,  # 後續可接 ResourceScaffold 查詢
        }

    def _get_neighbor_nodes(self, node: KnowledgeNode, user_id: uuid.UUID) -> list[dict]:
        """pgvector cosine similarity 查詢 top-3 鄰居（同科目過濾）。"""
        if node.embedding is None:
            return []

        try:
            rows = self.db.execute(
                text("""
                    SELECT kn.id, kn.name,
                           1 - (kn.embedding <=> :emb) AS similarity
                    FROM knowledge_nodes kn
                    WHERE kn.subject_id = :subject_id
                      AND kn.id != :node_id
                      AND kn.embedding IS NOT NULL
                    ORDER BY kn.embedding <=> :emb
                    LIMIT 3
                """),
                {
                    "emb": str(node.embedding),
                    "subject_id": str(node.subject_id),
                    "node_id": str(node.id),
                },
            ).fetchall()
        except Exception as e:
            log.warning("鄰居節點查詢失敗: %s", e)
            return []

        neighbors = []
        for row in rows:
            mastery = self.db.query(NodeMastery).filter(
                NodeMastery.user_id == user_id,
                NodeMastery.node_id == row[0],
            ).first()
            neighbors.append({
                "name": str(row[1])[:50],  # token 控制
                "similarity": round(float(row[2]), 2),
                "student_mastery": mastery.base_mastery if mastery else 0.0,
            })
        return neighbors

    def _count_subject_questions(self, subject_id: Optional[uuid.UUID]) -> int:
        """統計科目總題數。"""
        if not subject_id:
            return 0
        try:
            from app.models.question import Question
            from app.models.exam import Exam
            count = self.db.query(func.count()).select_from(
                Question
            ).join(
                Exam, Exam.id == Question.exam_id
            ).filter(
                Exam.subject_id == subject_id
            ).scalar()
            return count or 0
        except Exception:
            return 0

    def _compute_frequency_percentile(
        self, node_id: uuid.UUID, subject_id: Optional[uuid.UUID]
    ) -> int:
        """計算節點出題頻率百分位（0-100）。"""
        if not subject_id:
            return 0
        try:
            all_nodes = self.db.query(KnowledgeNode.available_questions).filter(
                KnowledgeNode.subject_id == subject_id,
                KnowledgeNode.available_questions > 0,
            ).all()
            if not all_nodes:
                return 0
            target_node = self.db.query(KnowledgeNode).filter(
                KnowledgeNode.id == node_id
            ).first()
            target_count = target_node.available_questions if target_node else 0
            counts = sorted([r[0] for r in all_nodes])
            rank = sum(1 for c in counts if c <= target_count)
            return int(rank / len(counts) * 100)
        except Exception:
            return 0

    def _build_context_summary(self, context: dict) -> dict:
        """給 API 回傳的精簡 context 摘要（不洩漏完整 context）。"""
        node = context.get("node", {})
        freq = context.get("exam_frequency", {})
        neighbors = context.get("neighbor_nodes", [])
        return {
            "node_name": node.get("name"),
            "subject_name": node.get("subject_name"),
            "frequency_percentile": freq.get("frequency_percentile", 0),
            "neighbor_count": len(neighbors),
            "has_scaffold": context.get("ai_scaffold_available", False),
        }

    def _call_llm_opening(self, model: str, context: dict) -> str:
        """呼叫 LLM 產生第一句引導問句。"""
        context_json = json.dumps(context, ensure_ascii=False)
        try:
            client = _get_anthropic()
            response = client.messages.create(
                model=model,
                max_tokens=400,
                system=SYSTEM_PROMPT_SOCRATIC,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"學生剛點擊了一個 orphan 節點，以下是完整 context，"
                            f"請產生蘇格拉底式開場引導問句：\n\n{context_json}"
                        ),
                    }
                ],
            )
            return response.content[0].text
        except Exception as e:
            log.error("LLM opening message 失敗: %s", e)
            node_name = context.get("node", {}).get("name", "這個概念")
            neighbors = context.get("neighbor_nodes", [])
            neighbor_mention = (
                f"你對「{neighbors[0]['name']}」應該有些印象，" if neighbors else ""
            )
            return (
                f"我們來聊聊「{node_name}」吧！"
                f"{neighbor_mention}"
                f"你覺得這個概念可能跟你學過的哪些知識有關聯呢？"
            )

    def _call_llm_continue(
        self,
        model: str,
        context: dict,
        conversation_history: list[dict],
        last_scores: dict,
    ) -> str:
        """呼叫 LLM 根據對話歷史繼續引導。"""
        context_json = json.dumps(context, ensure_ascii=False)
        score_hint = (
            f"（上一輪評分：概念接觸度={last_scores['concept']}，"
            f"推理連結度={last_scores['reasoning']}，"
            f"主動性={last_scores['initiative']}）"
        )
        system_with_context = (
            f"{SYSTEM_PROMPT_SOCRATIC}\n\n"
            f"【當前對話 Context】\n{context_json}\n\n"
            f"【上一輪學生回答評分提示】{score_hint}\n"
            f"根據評分調整你的提問深度：若概念接觸度=0，換更基礎的問法；"
            f"若概念接觸度=1，可稍微加深。"
        )
        try:
            client = _get_anthropic()
            response = client.messages.create(
                model=model,
                max_tokens=350,
                system=system_with_context,
                messages=conversation_history,
            )
            return response.content[0].text
        except Exception as e:
            log.error("LLM continue message 失敗: %s", e)
            return "你剛才的回應很有意思！可以再多說一點嗎？從你知道的角度切入就好。"

    def _build_conversation_history(
        self, all_messages: list, new_user_text: str
    ) -> list[dict]:
        """將 DB 訊息 + 本次 user 輸入組成 Anthropic messages 格式。"""
        history = []
        for m in all_messages:
            if m.role in ("user", "assistant"):
                history.append({"role": m.role, "content": m.content})
        history.append({"role": "user", "content": new_user_text})
        return history

    def _evaluate_turn(self, user_text: str, ai_question: str) -> dict:
        """C.3 評分：概念接觸度(LLM) + 推理連結度(LLM) + 主動性(規則)。"""
        # 主動性：規則判斷（≥ 20 字且非隨機輸入）
        initiative = self._score_initiative(user_text)

        # 若學生說「我不知道」類似極短回覆，不呼叫 LLM
        clean_text = user_text.strip()
        if len(clean_text) < 5 or clean_text in ("不知道", "不清楚", "沒概念", "?", "？"):
            return {
                "concept": 0.0,
                "reasoning": 0.0,
                "initiative": initiative,
                "total": initiative,
            }

        # LLM 評分概念接觸度 + 推理連結度
        prompt = build_evaluator_prompt(ai_question, user_text)
        try:
            client = _get_anthropic()
            response = client.messages.create(
                model=MODEL_HAIKU,  # 評分永遠用 Haiku 降成本
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            # 清除 markdown code block
            raw = re.sub(r"```(?:json)?", "", raw).strip()
            scores_json = json.loads(raw)
            concept = float(scores_json.get("concept", 0))
            reasoning = float(scores_json.get("reasoning", 0))
            # 合法值檢查
            concept = concept if concept in (0.0, 0.5, 1.0) else 0.0
            reasoning = reasoning if reasoning in (0.0, 0.5, 1.0) else 0.0
        except Exception as e:
            log.warning("LLM 評分失敗，降級為 0: %s", e)
            concept, reasoning = 0.0, 0.0

        total = concept + reasoning + initiative
        return {
            "concept": concept,
            "reasoning": reasoning,
            "initiative": initiative,
            "total": round(total, 1),
        }

    def _score_initiative(self, user_text: str) -> float:
        """主動性規則：≥ 20 字且非隨機輸入 → 0.5，否則 0。"""
        text = user_text.strip()
        if len(text) < INITIATIVE_MIN_CHARS:
            return 0.0
        if _RANDOM_INPUT_RE.match(text):
            return 0.0
        return 0.5

    def _check_end_conditions(
        self,
        round_number: int,
        all_scores: list[dict],
        node: Optional[KnowledgeNode],
    ) -> dict:
        """C.4 判斷對話是否應該結束。

        Returns:
            {should_end: bool, reason: str | None}
            reason: positive_close | transfer_book | switch_to_question |
                    force_end_8_rounds | None
        """
        # C.4.4 強制結束（8 輪）
        if round_number >= FORCE_END_ROUNDS:
            return {"should_end": True, "reason": "force_end_8_rounds"}

        # C.4.2 5 輪後仍零概念接觸 → 轉介書籍
        if round_number >= TRANSFER_BOOK_ZERO_ROUNDS:
            all_zero = all(s.get("round_score", 0) == 0 for s in all_scores)
            if all_zero:
                return {"should_end": True, "reason": "transfer_book"}

        # C.4.1 自然結束（正向）：最近一輪 ≥ 1.5/2.5
        latest_score = all_scores[-1].get("round_score", 0) if all_scores else 0
        if round_number >= 3 and latest_score >= POSITIVE_CLOSE_MIN_SCORE:
            return {"should_end": True, "reason": "positive_close"}

        # C.4.3 累計 ≥ 3 輪且得分 ≥ 1.0 → 插入考古題
        if round_number >= SWITCH_QUESTION_MIN_ROUNDS and latest_score >= SWITCH_QUESTION_MIN_SCORE:
            return {"should_end": True, "reason": "switch_to_question"}

        return {"should_end": False, "reason": None}

    def _build_closing_reply(
        self,
        reason: str,
        node: Optional[KnowledgeNode],
        scores: list[dict],
    ) -> str:
        """根據結束原因產生收尾語。"""
        node_name = node.name if node else "這個節點"
        question_count = node.available_questions if node else 0

        if reason == "positive_close":
            return build_closing_positive(
                concept=node_name,
                question_count=question_count,
                scaffold_available=False,
            )
        elif reason == "transfer_book":
            return build_closing_transfer_book(node_name=node_name)
        elif reason == "switch_to_question":
            return build_closing_switch_question(node_name=node_name)
        elif reason == "force_end_8_rounds":
            return build_closing_force_end(node_name=node_name)
        return "今日探索到這裡，我們改天繼續！"

    def _commit_mastery_if_eligible(
        self,
        session: AiChatSession,
        all_scores: list[dict],
    ) -> None:
        """C.3.2 若滿足條件則降權寫入 mastery。

        條件：
          - 對話至少 3 輪
          - 至少 2 輪得分 ≥ 1.5/2.5
          - 尚未 committed
        """
        if session.mastery_committed:
            return
        if not session.node_id:
            return

        round_count = len(all_scores)
        if round_count < MASTERY_COMMIT_MIN_ROUNDS:
            return

        high_score_rounds = sum(
            1 for s in all_scores
            if (s.get("round_score") or 0) >= POSITIVE_CLOSE_MIN_SCORE
        )
        if high_score_rounds < MASTERY_COMMIT_MIN_HIGH_ROUNDS:
            return

        # 計算降權後的 mastery 貢獻
        total_score = sum(s.get("round_score") or 0 for s in all_scores)
        avg_score = total_score / round_count if round_count > 0 else 0
        mastery_contribution = (avg_score / 2.5) * MASTERY_DISCOUNT

        # Upsert NodeMastery
        mastery = self.db.query(NodeMastery).filter(
            NodeMastery.user_id == session.user_id,
            NodeMastery.node_id == session.node_id,
        ).first()

        now = datetime.now(timezone.utc)
        next_review = now + timedelta(days=int(EFACTOR_SOCRATIC))

        if mastery:
            new_base = min(1.0, mastery.base_mastery + mastery_contribution)
            mastery.base_mastery = new_base
            mastery.ease_factor = EFACTOR_SOCRATIC
            mastery.last_tested_at = now
            mastery.next_review_at = next_review
            mastery.status = "PENDING" if new_base < 0.8 else "MASTERED"
        else:
            mastery = NodeMastery(
                user_id=session.user_id,
                node_id=session.node_id,
                base_mastery=mastery_contribution,
                ease_factor=EFACTOR_SOCRATIC,
                last_tested_at=now,
                next_review_at=next_review,
                status="PENDING",
            )
            self.db.add(mastery)

        session.mastery_committed = True
        log.info(
            "mastery committed: user=%s node=%s contribution=%.3f",
            session.user_id,
            session.node_id,
            mastery_contribution,
        )

    def _derive_status(
        self,
        session: AiChatSession,
        user_round_count: int,
        user_msgs: list,
    ) -> str:
        """從 session 狀態推導對話 status 字串。"""
        if session.mastery_committed:
            return "positive_close"
        if user_round_count >= MAX_ROUNDS:
            return "force_end"
        if session.paused_at:
            return "paused"
        if user_round_count == 0:
            return "started"
        return "continuing"
