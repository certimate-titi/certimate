"""Given setup — Feature 52 筆記 hashtag 系統 BDD."""

import uuid

from behave import given

from app.models.subject import Subject, SubjectCategory
from app.models.user_note import UserNote
from app.models.user_note_tag import UserNoteTag
from app.utils.markdown_hashtags import extract_hashtags


def _ensure_category(db) -> uuid.UUID:
    cat = db.query(SubjectCategory).filter_by(name="TestCat52").first()
    if cat is None:
        cat = SubjectCategory(name="TestCat52")
        db.add(cat)
        db.flush()
    return cat.id


def _make_subject(db, name: str) -> Subject:
    existing = db.query(Subject).filter_by(name=name).first()
    if existing:
        return existing
    cat_id = _ensure_category(db)
    subj = Subject(name=name, category_id=cat_id)
    db.add(subj)
    db.flush()
    return subj


def _create_note_with_tags(db, user_id: uuid.UUID, subject_id: uuid.UUID, content: str) -> UserNote:
    """建立 note 並同步解析 hashtag 至 user_note_tags。"""
    note = UserNote(
        user_id=user_id,
        subject_id=subject_id,
        content=content.strip(),
    )
    db.add(note)
    db.flush()

    for normalized, display in extract_hashtags(content):
        tag = UserNoteTag(
            note_id=note.id,
            tag_normalized=normalized,
            tag_display=display,
        )
        db.add(tag)

    db.commit()
    db.refresh(note)
    return note


# ── Background steps ──────────────────────────────────────────────────────────

@given('已存在科目 "{subject_name}" second_subject_id 存於 memo["second_subject_id"]')
def step_create_second_subject_into_memo(context, subject_name):
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}
    subj = _make_subject(db, subject_name)
    db.commit()
    context.memo["second_subject_id"] = str(subj.id)


# ── Given steps for F52 Scenarios ─────────────────────────────────────────────

@given('alice 已建立含 "{content}" 的筆記 id 存於 memo["note_id"]')
def step_alice_note_with_content_in_memo(context, content):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    subject_id = uuid.UUID(context.memo["subject_id"])
    note = _create_note_with_tags(db, user_id, subject_id, content)
    context.memo["note_id"] = str(note.id)


@given('alice 已建立含各種 hashtag 的多筆筆記')
def step_alice_multiple_notes_with_hashtags(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    subject_id = uuid.UUID(context.memo["subject_id"])

    contents = [
        "#機器學習 基礎概念介紹",
        "#深度學習 #神經網路 進階應用",
        "#資安 基本知識",
    ]
    for content in contents:
        _create_note_with_tags(db, user_id, subject_id, content)


@given('alice 已建立 subject_id 科目的筆記含 "#{tag_text}"')
def step_alice_note_subject_with_tag(context, tag_text):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    subject_id = uuid.UUID(context.memo["subject_id"])
    content = f"#{tag_text} 這是屬於 subject_id 科目的筆記內容"
    _create_note_with_tags(db, user_id, subject_id, content)


@given('alice 已建立 second_subject_id 科目的筆記含 "#{tag_text}"')
def step_alice_note_second_subject_with_tag(context, tag_text):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    second_subject_id = uuid.UUID(context.memo["second_subject_id"])
    content = f"#{tag_text} 這是屬於 second_subject_id 科目的筆記內容"
    _create_note_with_tags(db, user_id, second_subject_id, content)


@given('alice 已建立含 "#{tag_text}" 的筆記')
def step_alice_note_with_tag_no_memo(context, tag_text):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    subject_id = uuid.UUID(context.memo["subject_id"])
    content = f"#{tag_text} 筆記內容"
    _create_note_with_tags(db, user_id, subject_id, content)
