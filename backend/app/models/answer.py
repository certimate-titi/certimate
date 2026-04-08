"""Answer ORM Model — derived from erm.dbml.

欄位級加密（Phase 2）：
- selected_answer 在寫入前應透過 app.core.field_encryption.encrypt_field() 加密
- 讀取時透過 decrypt_field() 解密；is_answer_encrypted 旗標記錄加密狀態
- 欄位長度由 String(10) 調整為 String(512) 以容納 Fernet token（~180 chars）
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class Answer(Base):
    __tablename__ = "answers"
    __table_args__ = (
        UniqueConstraint("exam_id", "question_id", "user_id", name="uq_answers_exam_question_user"),
        {"comment": "學生作答紀錄（含欄位級加密保護 selected_answer）"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # 欄位長度擴展至 512 以容納 Fernet token（正常 token 約 180 chars）
    selected_answer: Mapped[Optional[str]] = mapped_column(
        String(512),
        comment="作答選項（加密時存儲 enc:{fernet_token}；is_answer_encrypted=True）",
    )
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean)
    confidence: Mapped[Optional[str]] = mapped_column(String(10))  # high/medium/low
    marked_for_review: Mapped[bool] = mapped_column(Boolean, default=False)
    answered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ── 欄位級加密 metadata（migration 041）────────────────────────────
    is_answer_encrypted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="selected_answer 是否已使用 Fernet 加密",
    )
    encrypted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="欄位加密時間戳記（稽核用）",
    )

    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True,
        comment="多租戶隔離鍵（NULL = 歸屬 public_b2c）— RLS 強制啟用（含個資）",
        index=True,
    )

    # ── 便利屬性：透明加解密 ────────────────────────────────────────────
    def get_plain_answer(self) -> Optional[str]:
        """取得解密後的作答選項（透明解密）。"""
        if self.selected_answer is None:
            return None
        if not self.is_answer_encrypted:
            return self.selected_answer
        from app.core.field_encryption import decrypt_field
        return decrypt_field(self.selected_answer)

    def set_encrypted_answer(self, plain_answer: Optional[str]) -> None:
        """設定並加密作答選項（透明加密）。"""
        if plain_answer is None:
            self.selected_answer = None
            self.is_answer_encrypted = False
            self.encrypted_at = None
            return
        from app.core.field_encryption import encrypt_field
        from datetime import timezone
        encrypted = encrypt_field(plain_answer)
        self.selected_answer = encrypted
        self.is_answer_encrypted = True
        self.encrypted_at = datetime.now(tz=timezone.utc)
