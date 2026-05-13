"""Then DB assertions — Feature 49 Chat Annotations BDD."""

import uuid

from behave import then

from app.models.chat_message_annotation import ChatMessageAnnotation


@then('DB 中 chat_message_annotations 新增一筆')
def step_assert_annotation_in_db(context):
    db = context.db_session
    annotation_id = context.memo.get("annotation_id")
    assert annotation_id, "annotation_id 不在 memo 中"

    ann = (
        db.query(ChatMessageAnnotation)
        .filter(ChatMessageAnnotation.id == uuid.UUID(annotation_id))
        .first()
    )
    assert ann is not None, f"DB 中找不到 annotation id={annotation_id}"
    assert len(ann.user_annotation) >= 10, "user_annotation 長度不足 10"


@then('DB 中該筆 annotation 已刪除')
def step_assert_annotation_deleted(context):
    db = context.db_session
    annotation_id = context.memo.get("annotation_id")
    assert annotation_id, "annotation_id 不在 memo 中"

    # 重新從 DB 撈（確保不用 cache）
    db.expire_all()
    ann = (
        db.query(ChatMessageAnnotation)
        .filter(ChatMessageAnnotation.id == uuid.UUID(annotation_id))
        .first()
    )
    assert ann is None, f"DB 中 annotation id={annotation_id} 應已刪除但仍存在"
