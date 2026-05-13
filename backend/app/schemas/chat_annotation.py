"""Pydantic v2 schemas for Chat Message Annotations."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

AnnotationType = Literal["note", "key_insight", "challenge", "example", "application"]

VALID_ANNOTATION_TYPES = {"note", "key_insight", "challenge", "example", "application"}


class ChatAnnotationCreate(BaseModel):
    """POST /api/v1/chat-annotations request body."""

    model_config = ConfigDict(from_attributes=True)

    message_id: UUID
    session_id: UUID
    highlighted_text: str = Field(..., min_length=1, max_length=5000)
    user_annotation: str = Field(..., min_length=10, max_length=2000)
    annotation_type: AnnotationType = "note"


class ChatAnnotationResponse(BaseModel):
    """Single annotation response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    message_id: UUID
    user_id: UUID
    session_id: UUID
    highlighted_text: str
    user_annotation: str
    annotation_type: AnnotationType
    created_at: datetime


class ChatAnnotationListResponse(BaseModel):
    """GET /api/v1/chat-annotations response."""

    model_config = ConfigDict(from_attributes=True)

    items: list[ChatAnnotationResponse]
    total: int
