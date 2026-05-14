"""Then — Feature 55 Tag Backfill DB assertions."""

import uuid

from behave import then
from sqlalchemy import text


@then('user_note_tags 表對 memo["legacy_note_id"] 有 {count:d} 筆 tag_normalized="{normalized}"')
def step_user_note_tags_has_tag(context, count, normalized):
    """驗證 user_note_tags 表存在指定 note 的 tag。"""
    db = context.db_session
    note_id = context.memo["legacy_note_id"]
    rows = db.execute(
        text(
            "SELECT COUNT(*) FROM user_note_tags WHERE note_id = :note_id AND tag_normalized = :normalized"
        ),
        {"note_id": note_id, "normalized": normalized},
    ).scalar_one()
    assert rows == count, (
        f"Expected {count} row(s) in user_note_tags for note_id={note_id} "
        f"tag_normalized={normalized!r}, got {rows}"
    )


@then('user_note_tags 表對 memo["legacy_note_id"] 恰好有 {count:d} 筆 tag_normalized="{normalized}"')
def step_user_note_tags_exactly(context, count, normalized):
    """重複執行後確認冪等（不重複寫入）。"""
    db = context.db_session
    note_id = context.memo["legacy_note_id"]
    rows = db.execute(
        text(
            "SELECT COUNT(*) FROM user_note_tags WHERE note_id = :note_id AND tag_normalized = :normalized"
        ),
        {"note_id": note_id, "normalized": normalized},
    ).scalar_one()
    assert rows == count, (
        f"Idempotent check failed: expected exactly {count} row(s), got {rows} "
        f"(note_id={note_id}, normalized={normalized!r})"
    )
