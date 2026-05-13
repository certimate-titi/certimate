"""DB assertions — Feature 54 Tags 3 Sources BDD."""

import uuid

from behave import then

from app.models.chat_annotation_tag import ChatAnnotationTag
from app.models.scaffold_tag import ScaffoldTag


@then('DB 中 chat_annotation_tags 包含 annotation_id 對應的 tag_normalized "{tag_normalized}"')
def step_assert_annotation_tag_exists(context, tag_normalized):
    db = context.db_session
    annotation_id = uuid.UUID(context.memo["annotation_id"])
    tag = (
        db.query(ChatAnnotationTag)
        .filter_by(annotation_id=annotation_id, tag_normalized=tag_normalized)
        .first()
    )
    assert tag is not None, f"DB 中 chat_annotation_tags 找不到 annotation_id={annotation_id} tag_normalized={tag_normalized}"


@then('DB 中 chat_annotation_tags 包含 tag "{tag_normalized}"')
def step_assert_annotation_tag_normalized_exists(context, tag_normalized):
    db = context.db_session
    annotation_id = uuid.UUID(context.memo["annotation_id"])
    tag = (
        db.query(ChatAnnotationTag)
        .filter_by(annotation_id=annotation_id, tag_normalized=tag_normalized)
        .first()
    )
    assert tag is not None, f"DB 中 chat_annotation_tags 找不到 tag_normalized={tag_normalized}"


@then('DB 中 chat_annotation_tags 不含 tag "{tag_normalized}"')
def step_assert_annotation_tag_not_exists(context, tag_normalized):
    db = context.db_session
    annotation_id = uuid.UUID(context.memo["annotation_id"])
    tag = (
        db.query(ChatAnnotationTag)
        .filter_by(annotation_id=annotation_id, tag_normalized=tag_normalized)
        .first()
    )
    assert tag is None, f"DB 中 chat_annotation_tags 應不含 tag_normalized={tag_normalized}，但找到了"


@then('DB 中 chat_annotation_tags 對此 annotation_id 共 0 筆')
def step_assert_annotation_tags_zero(context):
    db = context.db_session
    annotation_id = uuid.UUID(context.memo["annotation_id"])
    count = (
        db.query(ChatAnnotationTag)
        .filter_by(annotation_id=annotation_id)
        .count()
    )
    assert count == 0, f"DB 中 chat_annotation_tags 應有 0 筆，實際有 {count} 筆"


@then('DB 中 scaffold_tags 包含 scaffold_id 對應的 tag_normalized "{tag_normalized}" 且 user_id 為 alice')
def step_assert_scaffold_tag_with_user(context, tag_normalized):
    db = context.db_session
    scaffold_id = uuid.UUID(context.memo["scaffold_id"])
    user_id = uuid.UUID(context.ids["alice@example.com"])
    tag = (
        db.query(ScaffoldTag)
        .filter_by(scaffold_id=scaffold_id, user_id=user_id, tag_normalized=tag_normalized)
        .first()
    )
    assert tag is not None, (
        f"DB 中 scaffold_tags 找不到 scaffold_id={scaffold_id} user_id={user_id} tag_normalized={tag_normalized}"
    )


@then('DB 中 scaffold_tags 包含 tag "{tag_normalized}"')
def step_assert_scaffold_tag_exists(context, tag_normalized):
    db = context.db_session
    scaffold_id = uuid.UUID(context.memo["scaffold_id"])
    user_id = uuid.UUID(context.ids["alice@example.com"])
    tag = (
        db.query(ScaffoldTag)
        .filter_by(scaffold_id=scaffold_id, user_id=user_id, tag_normalized=tag_normalized)
        .first()
    )
    assert tag is not None, f"DB 中 scaffold_tags 找不到 tag_normalized={tag_normalized}"


@then('DB 中 scaffold_tags 不含 tag "{tag_normalized}"')
def step_assert_scaffold_tag_not_exists(context, tag_normalized):
    db = context.db_session
    scaffold_id = uuid.UUID(context.memo["scaffold_id"])
    user_id = uuid.UUID(context.ids["alice@example.com"])
    tag = (
        db.query(ScaffoldTag)
        .filter_by(scaffold_id=scaffold_id, user_id=user_id, tag_normalized=tag_normalized)
        .first()
    )
    assert tag is None, f"DB 中 scaffold_tags 應不含 tag_normalized={tag_normalized}，但找到了"


@then('DB 中 scaffold_tags 對此 scaffold_id 共 0 筆')
def step_assert_scaffold_tags_zero(context):
    db = context.db_session
    scaffold_id = uuid.UUID(context.memo["scaffold_id"])
    count = db.query(ScaffoldTag).filter_by(scaffold_id=scaffold_id).count()
    assert count == 0, f"DB 中 scaffold_tags 應有 0 筆，實際有 {count} 筆"
