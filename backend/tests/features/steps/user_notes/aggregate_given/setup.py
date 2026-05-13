"""Given setup — Feature 50 User Notes BDD."""

import uuid

from behave import given

from app.models.knowledge_node import KnowledgeNode
from app.models.resource import Resource
from app.models.resource_scaffold import ResourceScaffold, ResourceScaffoldType
from app.models.subject import Subject, SubjectCategory
from app.models.user import SubscriptionPlan, User, UserRole, UserStatus
from app.models.user_note import UserNote


def _ensure_user(db, email: str, plan: str = "FREE") -> uuid.UUID:
    """建立或取得用戶，回傳 user_id UUID。"""
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
        password_hash="test-hash",
        subscription_plan=plan_map.get(plan, SubscriptionPlan.FREE),
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.flush()
    return user.id


def _ensure_category(db) -> uuid.UUID:
    cat = db.query(SubjectCategory).filter_by(name="TestCat50").first()
    if cat is None:
        cat = SubjectCategory(name="TestCat50")
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


def _make_node(db, name: str, subject_id: uuid.UUID) -> KnowledgeNode:
    existing = db.query(KnowledgeNode).filter_by(name=name, subject_id=subject_id).first()
    if existing:
        return existing
    node = KnowledgeNode(
        name=name,
        subject_id=subject_id,
        depth=1,
    )
    db.add(node)
    db.flush()
    return node


# ── Background steps ──────────────────────────────────────────────────────────

@given('已存在科目 "{subject_name}" subject_id 存於 memo["subject_id"]')
def step_create_subject_into_memo(context, subject_name):
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}
    subj = _make_subject(db, subject_name)
    db.commit()
    context.memo["subject_id"] = str(subj.id)


@given('已存在知識節點 "{node_name}" node_id 存於 memo["node_id"]，屬於該科目')
def step_create_node_into_memo(context, node_name):
    db = context.db_session
    subject_id = uuid.UUID(context.memo["subject_id"])
    node = _make_node(db, node_name, subject_id)
    db.commit()
    context.memo["node_id"] = str(node.id)


# ── alice 筆記 given ──────────────────────────────────────────────────────────

@given('alice 已建立 3 筆不同科目的筆記')
def step_alice_3_notes_different_subjects(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    cat_id = _ensure_category(db)

    for i in range(3):
        subj_name = f"F50-Subject-{i}"
        subj = db.query(Subject).filter_by(name=subj_name).first()
        if subj is None:
            subj = Subject(name=subj_name, category_id=cat_id)
            db.add(subj)
            db.flush()

        note = UserNote(
            user_id=user_id,
            subject_id=subj.id,
            content=f"筆記內容 {i+1}，這是自動建立的測試筆記",
        )
        db.add(note)
    db.commit()


@given('alice 已建立 2 筆屬於 subject_id 的筆記')
def step_alice_2_notes_for_subject(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    subject_id = uuid.UUID(context.memo["subject_id"])

    for i in range(2):
        note = UserNote(
            user_id=user_id,
            subject_id=subject_id,
            content=f"屬於 subject 的筆記 {i+1}，內容完整",
        )
        db.add(note)
    db.commit()


@given('alice 已建立 1 筆筆記 id 存於 memo["note_id"]')
def step_alice_1_note_in_memo(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    subject_id = uuid.UUID(context.memo["subject_id"])

    note = UserNote(
        user_id=user_id,
        subject_id=subject_id,
        content="這是 alice 建立的測試筆記，內容超過一個字元",
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    context.memo["note_id"] = str(note.id)


@given('alice 已建立 1 筆筆記 id 存於 memo["alice_note_id"]')
def step_alice_1_note_alice_id(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    subject_id = uuid.UUID(context.memo["subject_id"])

    note = UserNote(
        user_id=user_id,
        subject_id=subject_id,
        content="alice 的筆記，bob 不應能修改或刪除",
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    context.memo["alice_note_id"] = str(note.id)


# ── scaffold given ────────────────────────────────────────────────────────────

@given('alice 有一個資源 resource_id 存於 memo["resource_id"]')
def step_alice_has_resource(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    subject_id = uuid.UUID(context.memo["subject_id"])

    resource = Resource(
        user_id=user_id,
        subject_id=subject_id,
        name="F50-TestResource",
        type="pdf",
        status="COMPLETED",
        file_size_bytes=1024,
        gcs_path="test/f50_resource.pdf",
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    context.memo["resource_id"] = str(resource.id)


@given('該資源有一個 scaffold id 存於 memo["scaffold_id"]')
def step_resource_has_scaffold(context):
    db = context.db_session
    resource_id = uuid.UUID(context.memo["resource_id"])

    scaffold = ResourceScaffold(
        resource_id=resource_id,
        type=ResourceScaffoldType.ELABORATIVE,
        content="測試鷹架的核心要點內容",
    )
    db.add(scaffold)
    db.commit()
    db.refresh(scaffold)
    context.memo["scaffold_id"] = str(scaffold.id)


# ── annotation given ──────────────────────────────────────────────────────────

@given('alice 已建立一筆 annotation id 存於 memo["annotation_id"]')
def step_alice_annotation_in_memo(context):
    from app.models.ai_chat import AiChatMessage, AiChatSession
    from app.models.chat_message_annotation import ChatMessageAnnotation

    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])

    # 建立 session + message
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
        content="AI 教練的測試回應",
    )
    db.add(message)
    db.flush()

    ann = ChatMessageAnnotation(
        message_id=message.id,
        user_id=user_id,
        session_id=session.id,
        highlighted_text="重要片段",
        user_annotation="這是一筆測試評語，字數超過十個字元以通過驗證",
        annotation_type="note",
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)
    context.memo["annotation_id"] = str(ann.id)
    context.memo["session_id"] = str(session.id)
    context.memo["message_id"] = str(message.id)
