"""AI Chat ORM Models — derived from erm.dbml."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class AiChatSession(Base):
    """AI 對話 Session（一個使用者在某個情境下開啟的對話串）。

    對應 DBML 表：ai_chat_sessions
    一對多關聯 ai_chat_messages（透過 session_id）。

    Attributes:
        user_id: 對應 users.id（CASCADE 刪除）
        context_type: 情境類型（例如 question / resource / mock_exam）
        context_id: 情境主鍵 UUID（依 context_type 解讀）
        model_used: 採用的 AI 模型名稱（例如 gemini-2.5-pro）
        message_count: 目前累積訊息數
        tenant_id: 多租戶隔離鍵（NULL 視為 public_b2c）
        mode: 對話模式（error_explanation | socratic_orphan，NULL = 舊資料相容）
        node_id: socratic_orphan 模式的目標 orphan 知識節點
        score_concept: 最新輪概念接觸度（0 / 0.5 / 1）
        score_reasoning: 最新輪推理連結度（0 / 0.5 / 1）
        score_initiative: 最新輪主動性（0 / 0.5）
        final_score: 最新輪總分（最高 2.5）
        mastery_committed: 是否已將蘇格拉底對話 mastery 降權寫入 node_mastery
        paused_at: C.4.4 3 分鐘無回應暫停時間，下次進入同節點自動接續
    """

    __tablename__ = "ai_chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    context_type: Mapped[str] = mapped_column(String(20), nullable=False)
    context_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    model_used: Mapped[str | None] = mapped_column(String(50))
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
        comment="多租戶隔離鍵（NULL = 歸屬 public_b2c）",
        index=True,
    )
    # ── Migration 094：Orphan Coach 蘇格拉底對話欄位 ──────────────
    mode: Mapped[str | None] = mapped_column(
        String(32), nullable=True,
        comment="對話模式：error_explanation | socratic_orphan（NULL = 舊資料相容）",
    )
    node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_nodes.id", ondelete="CASCADE"),
        nullable=True,
        comment="socratic_orphan 模式：目標 orphan 知識節點",
        index=True,
    )
    score_concept: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="最新輪概念接觸度評分（0/0.5/1）"
    )
    score_reasoning: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="最新輪推理連結度評分（0/0.5/1）"
    )
    score_initiative: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="最新輪主動性評分（0/0.5，規則判斷）"
    )
    final_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="最新輪總分（最高 2.5）"
    )
    mastery_committed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE",
        comment="是否已將蘇格拉底對話 mastery 降權寫入 node_mastery",
    )
    paused_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="C.4.4：3 分鐘無回應暫停時間，下次進入同節點自動接續",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AiChatMessage(Base):
    """AI 對話單則訊息。

    對應 DBML 表：ai_chat_messages
    從屬於 AiChatSession（session_id CASCADE 刪除）。

    Attributes:
        session_id: 所屬 session
        role: 訊息角色（user / assistant / system）
        content: 訊息文字內容
        token_count: 該訊息所耗 token 數（供成本帳明細）
        score_concept: 該輪概念接觸度（僅 user role 有值）
        score_reasoning: 該輪推理連結度（僅 user role 有值）
        score_initiative: 該輪主動性（僅 user role 有值）
        round_score: 該輪總分（最高 2.5，僅 user role 有值）
    """

    __tablename__ = "ai_chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_chat_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(10), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    # ── Migration 094：每輪評分（僅 user role 有值）────────────────
    score_concept: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="該輪概念接觸度（0/0.5/1）"
    )
    score_reasoning: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="該輪推理連結度（0/0.5/1）"
    )
    score_initiative: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="該輪主動性（0/0.5）"
    )
    round_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="該輪總分（最高 2.5）"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
