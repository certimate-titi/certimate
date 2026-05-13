"""Given setup — Feature 54 Tags 3 Sources BDD."""

import uuid
from datetime import date, timedelta

from behave import given

from app.models.ai_chat import AiChatMessage, AiChatSession
from app.models.chat_annotation_tag import ChatAnnotationTag
from app.models.chat_message_annotation import ChatMessageAnnotation
from app.models.learning_journey import LearningJourney, LearningMode, SelfAssessedLevel
from app.models.resource import Resource, ResourceStatus, ResourceType
from app.models.resource_scaffold import ResourceScaffold, ResourceScaffoldType
from app.models.scaffold_tag import ScaffoldTag
from app.models.subject import Subject, SubjectCategory
from app.models.user import SubscriptionPlan, User, UserRole, UserStatus
from app.models.user_note import UserNote
from app.models.user_note_tag import UserNoteTag
from app.utils.markdown_hashtags import extract_hashtags


# ── Helpers ─────────────────────────────────────────────────────────────────

def _ensure_user(db, email: str, plan: str = "PRO") -> uuid.UUID:
    plan_map = {
        "FREE": SubscriptionPlan.FREE,
        "PRO": SubscriptionPlan.PRO,
        "PRO_PLUS": SubscriptionPlan.PRO_PLUS,
    }
    existing = db.query(User).filter_by(email=email).first()
    if existing:
        return existing.id
    user = User(
        email=email,
        password_hash="test-hash-f54",
        subscription_plan=plan_map.get(plan, SubscriptionPlan.PRO),
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.flush()
    return user.id


def _ensure_category(db) -> uuid.UUID:
    cat = db.query(SubjectCategory).filter_by(name="TestCat54").first()
    if cat is None:
        cat = SubjectCategory(name="TestCat54")
        db.add(cat)
        db.flush()
    return cat.id


def _ensure_subject(db, name: str) -> Subject:
    existing = db.query(Subject).filter_by(name=name).first()
    if existing:
        return existing
    cat_id = _ensure_category(db)
    subj = Subject(name=name, category_id=cat_id)
    db.add(subj)
    db.flush()
    return subj


def _create_session_with_message(db, user_id: uuid.UUID):
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
        content="AI 教練回應內容。",
    )
    db.add(message)
    db.flush()
    return session, message


def _create_annotation_with_tags(db, user_id: uuid.UUID, session_id: uuid.UUID, message_id: uuid.UUID, user_annotation: str) -> ChatMessageAnnotation:
    ann = ChatMessageAnnotation(
        message_id=message_id,
        user_id=user_id,
        session_id=session_id,
        highlighted_text="重要片段",
        user_annotation=user_annotation,
        annotation_type="note",
    )
    db.add(ann)
    db.flush()
    for normalized, display in extract_hashtags(user_annotation):
        db.add(ChatAnnotationTag(
            annotation_id=ann.id,
            tag_normalized=normalized,
            tag_display=display,
        ))
    db.flush()
    return ann


def _create_resource_with_scaffold(db, user_id: uuid.UUID, subject_id: uuid.UUID) -> tuple:
    resource = Resource(
        user_id=user_id,
        subject_id=subject_id,
        title="測試資源",
        type=ResourceType.pdf,
        status=ResourceStatus.COMPLETED,
    )
    db.add(resource)
    db.flush()
    scaffold = ResourceScaffold(
        resource_id=resource.id,
        type=ResourceScaffoldType.ELABORATIVE,
        content="這是一個延伸思考題",
    )
    db.add(scaffold)
    db.flush()
    return resource, scaffold


def _create_scaffold_with_tags(db, user_id: uuid.UUID, subject_id: uuid.UUID, user_response: str) -> tuple:
    resource, scaffold = _create_resource_with_scaffold(db, user_id, subject_id)
    from datetime import datetime, timezone
    scaffold.user_response = user_response
    scaffold.responded_at = datetime.now(timezone.utc)
    db.flush()
    for normalized, display in extract_hashtags(user_response):
        db.add(ScaffoldTag(
            scaffold_id=scaffold.id,
            user_id=user_id,
            tag_normalized=normalized,
            tag_display=display,
        ))
    db.flush()
    return resource, scaffold


def _create_journey(db, user_id: uuid.UUID, subject_id: uuid.UUID, exam_date: date) -> LearningJourney:
    existing = db.query(LearningJourney).filter_by(user_id=user_id, subject_id=subject_id).first()
    if existing:
        existing.exam_date = exam_date
        db.flush()
        return existing
    journey = LearningJourney(
        user_id=user_id,
        subject_id=subject_id,
        exam_date=exam_date,
        self_assessed_level=SelfAssessedLevel.BEGINNER,
        learning_mode=LearningMode.STANDARD,
    )
    db.add(journey)
    db.flush()
    return journey


# ── Given: Session + Message ──────────────────────────────────────────────────

@given('alice 已有 AI 對話 session_id 存於 memo["session_id"]，含一則訊息 message_id 存於 memo["message_id"]')
def step_alice_has_session_and_message(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    session, message = _create_session_with_message(db, user_id)
    db.commit()
    context.memo["session_id"] = str(session.id)
    context.memo["message_id"] = str(message.id)


# ── Given: Existing Annotation with Tags ─────────────────────────────────────

@given('alice 已建立含 "{user_annotation}" 的 annotation annotation_id 存於 memo["annotation_id"]')
def step_alice_has_annotation_with_content(context, user_annotation):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    session_id = uuid.UUID(context.memo["session_id"])
    message_id = uuid.UUID(context.memo["message_id"])
    ann = _create_annotation_with_tags(db, user_id, session_id, message_id, user_annotation)
    db.commit()
    context.memo["annotation_id"] = str(ann.id)


@given('alice 已有含 "{user_annotation}" 的 annotation（已建立）')
def step_alice_has_annotation_already(context, user_annotation):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    # 確保有 session/message
    if "session_id" not in context.memo:
        session, message = _create_session_with_message(db, user_id)
        context.memo["session_id"] = str(session.id)
        context.memo["message_id"] = str(message.id)
    session_id = uuid.UUID(context.memo["session_id"])
    message_id = uuid.UUID(context.memo["message_id"])
    ann = _create_annotation_with_tags(db, user_id, session_id, message_id, user_annotation)
    db.commit()
    context.memo["annotation_id"] = str(ann.id)


# ── Given: Resource + Scaffold ───────────────────────────────────────────────

@given('alice 已有 resource_id 存於 memo["resource_id"]，含一個 scaffold scaffold_id 存於 memo["scaffold_id"]')
def step_alice_has_resource_and_scaffold(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    subject_id = uuid.UUID(context.memo["subject_id"])
    resource, scaffold = _create_resource_with_scaffold(db, user_id, subject_id)
    db.commit()
    context.memo["resource_id"] = str(resource.id)
    context.memo["scaffold_id"] = str(scaffold.id)


@given('alice 已 PATCH scaffold user_response 為 "{user_response}"')
def step_alice_patched_scaffold(context, user_response):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    scaffold_id = uuid.UUID(context.memo["scaffold_id"])
    from datetime import datetime, timezone
    scaffold = db.get(ResourceScaffold, scaffold_id)
    scaffold.user_response = user_response
    scaffold.responded_at = datetime.now(timezone.utc)
    db.flush()
    # 同步 tags
    for normalized, display in extract_hashtags(user_response):
        existing = db.query(ScaffoldTag).filter_by(
            scaffold_id=scaffold_id,
            user_id=user_id,
            tag_normalized=normalized,
        ).first()
        if not existing:
            db.add(ScaffoldTag(
                scaffold_id=scaffold_id,
                user_id=user_id,
                tag_normalized=normalized,
                tag_display=display,
            ))
    db.commit()


@given('alice 已有含 "{user_response}" 的 scaffold user_response（已建立）')
def step_alice_has_scaffold_response_already(context, user_response):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    subject_id = uuid.UUID(context.memo["subject_id"])
    resource, scaffold = _create_scaffold_with_tags(db, user_id, subject_id, user_response)
    db.commit()
    context.memo["scaffold_id"] = str(scaffold.id)
    context.memo["resource_id"] = str(resource.id)


# ── Given: User Note ─────────────────────────────────────────────────────────

@given('alice 已建立含 "{content}" 的 user note note_id 存於 memo["note_id"]')
def step_alice_has_note_f54(context, content):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    subject_id = uuid.UUID(context.memo["subject_id"])
    note = UserNote(user_id=user_id, subject_id=subject_id, content=content.strip())
    db.add(note)
    db.flush()
    for normalized, display in extract_hashtags(content):
        db.add(UserNoteTag(note_id=note.id, tag_normalized=normalized, tag_display=display))
    db.commit()
    context.memo["note_id"] = str(note.id)


@given('alice 已建立含 "{content}" 的 user note，subject_id 為 memo["subject_id"]')
def step_alice_has_note_with_subject1_f54(context, content):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    subject_id = uuid.UUID(context.memo["subject_id"])
    note = UserNote(user_id=user_id, subject_id=subject_id, content=content.strip())
    db.add(note)
    db.flush()
    for normalized, display in extract_hashtags(content):
        db.add(UserNoteTag(note_id=note.id, tag_normalized=normalized, tag_display=display))
    db.commit()


@given('alice 已建立含 "{content}" 的 user note，subject_id 為 memo["second_subject_id"]')
def step_alice_has_note_with_subject2_f54(context, content):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    subject_id = uuid.UUID(context.memo["second_subject_id"])
    note = UserNote(user_id=user_id, subject_id=subject_id, content=content.strip())
    db.add(note)
    db.flush()
    for normalized, display in extract_hashtags(content):
        db.add(UserNoteTag(note_id=note.id, tag_normalized=normalized, tag_display=display))
    db.commit()


@given('alice 已建立含 "{content}" 的 user note')
def step_alice_has_note_plain_f54(context, content):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    subject_id = uuid.UUID(context.memo["subject_id"])
    note = UserNote(user_id=user_id, subject_id=subject_id, content=content.strip())
    db.add(note)
    db.flush()
    for normalized, display in extract_hashtags(content):
        db.add(UserNoteTag(note_id=note.id, tag_normalized=normalized, tag_display=display))
    db.commit()


# ── Given: DB delete scaffold ────────────────────────────────────────────────

@given('DB 中刪除該 scaffold')
def step_delete_scaffold_from_db(context):
    db = context.db_session
    scaffold_id = uuid.UUID(context.memo["scaffold_id"])
    scaffold = db.get(ResourceScaffold, scaffold_id)
    if scaffold:
        db.delete(scaffold)
        db.commit()
