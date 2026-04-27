"""StudentGroup & StudentGroupMember ORM Models — derived from erm.dbml."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class StudentGroup(Base):
    """B2B 學生群組（一個機構底下的班級）。

    對應 DBML 表：student_groups
    一對多 student_group_members；institution CASCADE 刪除。

    Attributes:
        institution_id: 所屬機構（CASCADE）
        name: 群組名稱（例如 "資工三甲"）
    """

    __tablename__ = "student_groups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class StudentGroupMember(Base):
    """學生群組成員關聯。

    對應 DBML 表：student_group_members
    Unique（group_id, user_id）。

    Attributes:
        group_id: 群組（CASCADE）
        user_id: 使用者（CASCADE）
        joined_at: 加入時間
    """

    __tablename__ = "student_group_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_member"),
    )
