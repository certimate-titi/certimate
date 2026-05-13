"""Pydantic v2 schemas for User Notes — Feature 50 我的筆記整合 + Feature 52 hashtag 系統。"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserNoteCreate(BaseModel):
    """POST /api/v1/user-notes request body."""

    model_config = ConfigDict(from_attributes=True)

    subject_id: UUID
    node_id: UUID | None = None
    title: str | None = Field(None, max_length=200)
    content: str = Field(..., min_length=1, max_length=50000)


class UserNoteUpdate(BaseModel):
    """PATCH /api/v1/user-notes/{id} request body.

    至少提供 title 或 content 其中之一。
    """

    model_config = ConfigDict(from_attributes=True)

    title: str | None = Field(None, max_length=200)
    content: str | None = Field(None, min_length=1, max_length=50000)


class UserNoteResponse(BaseModel):
    """Single note response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    subject_id: UUID
    node_id: UUID | None
    title: str | None
    content: str
    created_at: datetime
    updated_at: datetime


class UserNoteListResponse(BaseModel):
    """GET /api/v1/user-notes response."""

    model_config = ConfigDict(from_attributes=True)

    items: list[UserNoteResponse]
    total: int


class UserNoteTagItem(BaseModel):
    """Single tag item in tag list response."""

    model_config = ConfigDict(from_attributes=True)

    normalized: str
    display: str
    count: int


class UserNoteTagListResponse(BaseModel):
    """GET /api/v1/user-notes/tags response."""

    model_config = ConfigDict(from_attributes=True)

    items: list[UserNoteTagItem]
    total: int
