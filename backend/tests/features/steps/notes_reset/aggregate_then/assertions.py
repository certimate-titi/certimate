"""Then — Feature 51 筆記重置斷言：DB 狀態 + response body。"""

import uuid

from behave import then

from app.models.chat_message_annotation import ChatMessageAnnotation
from app.models.resource import Resource
from app.models.resource_scaffold import ResourceScaffold
from app.models.user_note import UserNote


# ── response body 斷言 ────────────────────────────────────────────────────────

@then("response body 含 deleted={n:d}")
def step_response_body_deleted(context, n):
    data = context.last_response.json()
    assert data.get("deleted") == n, (
        f"expected deleted={n}, got {data.get('deleted')} | full={data}"
    )


@then("response body 含 cleared={n:d}")
def step_response_body_cleared(context, n):
    data = context.last_response.json()
    assert data.get("cleared") == n, (
        f"expected cleared={n}, got {data.get('cleared')} | full={data}"
    )


# ── DB user_notes 斷言 ────────────────────────────────────────────────────────

@then("DB 中 alice 的 user_notes 筆數為 0")
def step_db_alice_notes_zero(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    count = db.query(UserNote).filter(UserNote.user_id == user_id).count()
    assert count == 0, f"expected 0 alice notes in DB, got {count}"


@then("DB 中 bob 的 user_notes 筆數為 3")
def step_db_bob_notes_three(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["bob@example.com"])
    count = db.query(UserNote).filter(UserNote.user_id == user_id).count()
    assert count == 3, f"expected 3 bob notes in DB, got {count}"


# ── DB chat_annotations 斷言 ──────────────────────────────────────────────────

@then("DB 中 alice 的 chat_annotations 筆數為 0")
def step_db_alice_annotations_zero(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    count = (
        db.query(ChatMessageAnnotation)
        .filter(ChatMessageAnnotation.user_id == user_id)
        .count()
    )
    assert count == 0, f"expected 0 alice annotations in DB, got {count}"


@then("DB 中 bob 的 chat_annotations 筆數為 2")
def step_db_bob_annotations_two(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["bob@example.com"])
    count = (
        db.query(ChatMessageAnnotation)
        .filter(ChatMessageAnnotation.user_id == user_id)
        .count()
    )
    assert count == 2, f"expected 2 bob annotations in DB, got {count}"


# ── DB scaffold user_response 斷言 ────────────────────────────────────────────

@then("DB 中 alice 的 scaffold user_response 全為 NULL")
def step_db_alice_scaffold_responses_null(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])

    resource_ids = [
        r.id
        for r in db.query(Resource.id).filter(Resource.user_id == user_id).all()
    ]
    if not resource_ids:
        return  # 無 resource = 無 scaffold，斷言通過

    non_null_count = (
        db.query(ResourceScaffold)
        .filter(
            ResourceScaffold.resource_id.in_(resource_ids),
            ResourceScaffold.user_response.isnot(None),
        )
        .count()
    )
    assert non_null_count == 0, (
        f"expected 0 non-null user_response for alice, got {non_null_count}"
    )


@then("DB 中 bob 的 scaffold user_response 均不為 NULL")
def step_db_bob_scaffold_responses_not_null(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["bob@example.com"])

    resource_ids = [
        r.id
        for r in db.query(Resource.id).filter(Resource.user_id == user_id).all()
    ]
    assert resource_ids, "bob should have at least one resource"

    # 取 bob 有 user_response 的 scaffold 數
    non_null_count = (
        db.query(ResourceScaffold)
        .filter(
            ResourceScaffold.resource_id.in_(resource_ids),
            ResourceScaffold.user_response.isnot(None),
        )
        .count()
    )
    assert non_null_count > 0, (
        f"expected bob's scaffold user_response to remain non-null, but got {non_null_count}"
    )
