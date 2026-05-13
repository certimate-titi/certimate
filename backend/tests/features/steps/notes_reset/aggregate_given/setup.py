"""Given setup — Feature 51 筆記重置 BDD。

建立測試用的 user_notes、chat_annotations、resource_scaffolds。
"""

import uuid
from datetime import datetime, timezone

from behave import given

from app.models.chat_message_annotation import ChatMessageAnnotation
from app.models.ai_chat import AiChatMessage, AiChatSession
from app.models.resource import Resource
from app.models.resource_scaffold import ResourceScaffold, ResourceScaffoldType
from app.models.user_note import UserNote


def _get_user_id(context, email: str) -> uuid.UUID:
    return uuid.UUID(context.ids[email])


def _ensure_subject_id(context) -> uuid.UUID:
    return uuid.UUID(context.memo["subject_id"])


def _create_session_and_message(db, user_id: uuid.UUID):
    """建立一個 AiChatSession 及一則 AI message，回傳 (session, message)。"""
    session = AiChatSession(
        user_id=user_id,
        context_type="resource",
        context_id=uuid.uuid4(),
        model_used="gemini-2.5-pro",
        message_count=1,
    )
    db.add(session)
    db.flush()

    message = AiChatMessage(
        session_id=session.id,
        role="assistant",
        content="AI 教練測試回應，用於 Feature 51 重置測試。",
    )
    db.add(message)
    db.flush()
    return session, message


# ── user_notes Given ──────────────────────────────────────────────────────────

@given("alice 已建立 5 筆 user_notes")
def step_alice_5_user_notes(context):
    db = context.db_session
    user_id = _get_user_id(context, "alice@example.com")
    subject_id = _ensure_subject_id(context)

    for i in range(5):
        note = UserNote(
            user_id=user_id,
            subject_id=subject_id,
            content=f"F51 alice 筆記 {i + 1}，內容夠長通過驗證",
        )
        db.add(note)
    db.commit()


@given("alice 已建立 2 筆 user_notes")
def step_alice_2_user_notes(context):
    db = context.db_session
    user_id = _get_user_id(context, "alice@example.com")
    subject_id = _ensure_subject_id(context)

    for i in range(2):
        note = UserNote(
            user_id=user_id,
            subject_id=subject_id,
            content=f"F51 alice 筆記 {i + 1}",
        )
        db.add(note)
    db.commit()


@given("bob 已建立 3 筆 user_notes")
def step_bob_3_user_notes(context):
    db = context.db_session
    user_id = _get_user_id(context, "bob@example.com")
    subject_id = _ensure_subject_id(context)

    for i in range(3):
        note = UserNote(
            user_id=user_id,
            subject_id=subject_id,
            content=f"F51 bob 筆記 {i + 1}",
        )
        db.add(note)
    db.commit()


# ── chat_annotations Given ────────────────────────────────────────────────────

def _create_annotations_for_user(db, user_id: uuid.UUID, count: int):
    """為指定 user 建立 count 筆 chat_annotations（每個 session 最多 5 筆）。"""
    session, message = _create_session_and_message(db, user_id)
    for i in range(count):
        ann = ChatMessageAnnotation(
            message_id=message.id,
            user_id=user_id,
            session_id=session.id,
            highlighted_text=f"重要片段 {i + 1}",
            user_annotation=f"F51 測試評語第 {i + 1} 筆，確保字數達到十個字元以上",
            annotation_type="note",
        )
        db.add(ann)
    db.commit()


@given("alice 已建立 3 筆 chat_annotations")
def step_alice_3_chat_annotations(context):
    db = context.db_session
    user_id = _get_user_id(context, "alice@example.com")
    _create_annotations_for_user(db, user_id, 3)


@given("alice 已建立 1 筆 chat_annotations")
def step_alice_1_chat_annotation(context):
    db = context.db_session
    user_id = _get_user_id(context, "alice@example.com")
    _create_annotations_for_user(db, user_id, 1)


@given("bob 已建立 2 筆 chat_annotations")
def step_bob_2_chat_annotations(context):
    db = context.db_session
    user_id = _get_user_id(context, "bob@example.com")
    _create_annotations_for_user(db, user_id, 2)


# ── scaffold user_response Given ──────────────────────────────────────────────

def _make_resource(db, user_id: uuid.UUID, subject_id: uuid.UUID, name: str) -> Resource:
    r = Resource(
        user_id=user_id,
        subject_id=subject_id,
        name=name,
        type="pdf",
        status="COMPLETED",
        file_size_bytes=1024,
        gcs_path=f"test/f51/{name}.pdf",
    )
    db.add(r)
    db.flush()
    return r


def _make_scaffold_with_response(db, resource_id: uuid.UUID, idx: int) -> ResourceScaffold:
    s = ResourceScaffold(
        resource_id=resource_id,
        type=ResourceScaffoldType.ELABORATIVE,
        content=f"鷹架內容 {idx}",
        user_response=f"使用者作答 {idx}",
        responded_at=datetime.now(timezone.utc),
    )
    db.add(s)
    return s


@given("alice 有 2 個 resources 各含 user_response 的 scaffolds，共 5 筆有回應")
def step_alice_2_resources_5_scaffolds(context):
    db = context.db_session
    user_id = _get_user_id(context, "alice@example.com")
    subject_id = _ensure_subject_id(context)

    r1 = _make_resource(db, user_id, subject_id, "F51-alice-R1")
    for i in range(3):
        _make_scaffold_with_response(db, r1.id, i + 1)

    r2 = _make_resource(db, user_id, subject_id, "F51-alice-R2")
    for i in range(2):
        _make_scaffold_with_response(db, r2.id, i + 4)

    db.commit()


@given("alice 有 1 個 resource 含 2 筆 user_response scaffolds")
def step_alice_1_resource_2_scaffolds(context):
    db = context.db_session
    user_id = _get_user_id(context, "alice@example.com")
    subject_id = _ensure_subject_id(context)

    r = _make_resource(db, user_id, subject_id, "F51-alice-iso-R")
    for i in range(2):
        _make_scaffold_with_response(db, r.id, i + 1)
    db.commit()


@given("bob 有 1 個 resource 含 2 筆 user_response scaffolds")
def step_bob_1_resource_2_scaffolds(context):
    db = context.db_session
    user_id = _get_user_id(context, "bob@example.com")
    subject_id = _ensure_subject_id(context)

    r = _make_resource(db, user_id, subject_id, "F51-bob-iso-R")
    for i in range(2):
        _make_scaffold_with_response(db, r.id, i + 1)
    db.commit()
