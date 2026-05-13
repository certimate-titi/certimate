"""Then DB assertions — Feature 52 筆記 hashtag 系統 BDD."""

import uuid

from behave import then

from app.models.user_note_tag import UserNoteTag


def _get_tags_for_note(db, note_id: str) -> list[UserNoteTag]:
    """查詢指定 note_id 的所有 tags（note_id 傳入 str，內部轉 UUID）。"""
    return (
        db.query(UserNoteTag)
        .filter(UserNoteTag.note_id == uuid.UUID(note_id))
        .all()
    )


# ── tag 存在性 ────────────────────────────────────────────────────────────────

@then('DB 中 user_note_tags 包含 tag_normalized "{tag1}" 與 "{tag2}"')
def step_db_has_two_tags(context, tag1, tag2):
    note_id = context.memo.get("note_id") or context.memo.get("created_note", {}).get("id")
    assert note_id, "note_id 不存在於 memo"

    db = context.db_session
    tags = _get_tags_for_note(db, str(note_id))
    normalized_set = {t.tag_normalized for t in tags}

    assert tag1 in normalized_set, f"tag_normalized '{tag1}' 不在 DB 中，現有：{normalized_set}"
    assert tag2 in normalized_set, f"tag_normalized '{tag2}' 不在 DB 中，現有：{normalized_set}"


@then('DB 中 user_note_tags 包含 tag "{tag1}"、"{tag2}"、"{tag3}" 三個 normalized tag')
def step_db_has_three_tags(context, tag1, tag2, tag3):
    note_id = context.memo.get("note_id") or context.memo.get("created_note", {}).get("id")
    assert note_id, "note_id 不存在於 memo"

    db = context.db_session
    tags = _get_tags_for_note(db, str(note_id))
    normalized_set = {t.tag_normalized for t in tags}

    assert tag1 in normalized_set, f"tag_normalized '{tag1}' 不在 DB 中，現有：{normalized_set}"
    assert tag2 in normalized_set, f"tag_normalized '{tag2}' 不在 DB 中，現有：{normalized_set}"
    assert tag3 in normalized_set, f"tag_normalized '{tag3}' 不在 DB 中，現有：{normalized_set}"


@then('DB 中 user_note_tags 對此 note 共 0 筆')
def step_db_zero_tags(context):
    note_id = context.memo.get("note_id") or context.memo.get("created_note", {}).get("id")
    assert note_id, "note_id 不存在於 memo"

    db = context.db_session
    # 刷新 session 以確保讀到最新狀態
    db.expire_all()
    tags = _get_tags_for_note(db, str(note_id))
    assert len(tags) == 0, f"期望 0 筆 tag，實際 {len(tags)} 筆：{[t.tag_normalized for t in tags]}"


@then('DB 中 user_note_tags 對此 note 共 1 筆，tag_normalized 為 "{expected}"')
def step_db_exactly_one_tag(context, expected):
    note_id = context.memo.get("note_id") or context.memo.get("created_note", {}).get("id")
    assert note_id, "note_id 不存在於 memo"

    db = context.db_session
    tags = _get_tags_for_note(db, str(note_id))
    normalized_set = {t.tag_normalized for t in tags}

    assert len(tags) == 1, f"期望 1 筆 tag，實際 {len(tags)} 筆：{normalized_set}"
    assert expected in normalized_set, f"期望 tag_normalized='{expected}'，實際：{normalized_set}"


# ── update diff ───────────────────────────────────────────────────────────────

@then('DB 中 user_note_tags 不含 tag_normalized "{tag}"')
def step_db_not_contain_tag(context, tag):
    note_id = context.memo.get("note_id")
    assert note_id, "note_id 不存在於 memo"

    db = context.db_session
    tags = _get_tags_for_note(db, str(note_id))
    normalized_set = {t.tag_normalized for t in tags}

    assert tag not in normalized_set, f"tag_normalized '{tag}' 仍在 DB 中（應已移除），現有：{normalized_set}"


@then('DB 中 user_note_tags 包含 tag_normalized "{tag}"')
def step_db_contain_tag(context, tag):
    note_id = context.memo.get("note_id")
    assert note_id, "note_id 不存在於 memo"

    db = context.db_session
    tags = _get_tags_for_note(db, str(note_id))
    normalized_set = {t.tag_normalized for t in tags}

    assert tag in normalized_set, f"tag_normalized '{tag}' 不在 DB 中，現有：{normalized_set}"
