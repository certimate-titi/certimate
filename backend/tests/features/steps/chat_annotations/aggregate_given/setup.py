"""Given setup — Feature 49 Chat Annotations BDD."""

import uuid

from behave import given

from app.models.ai_chat import AiChatSession, AiChatMessage
from app.models.chat_message_annotation import ChatMessageAnnotation


def _ensure_user(db, email: str, plan: str = "PRO"):
    """取得或建立使用者，回傳 user_id (UUID)。"""
    from app.models.user import User, UserStatus, UserRole, SubscriptionPlan, SubscriptionStatus
    from app.services.auth_service import _hash_password

    PLAN_MAP = {
        "FREE": SubscriptionPlan.FREE,
        "PRO": SubscriptionPlan.PRO,
        "PRO_PLUS": SubscriptionPlan.PRO_PLUS,
        "ULTRA": SubscriptionPlan.ULTRA,
    }

    existing = db.query(User).filter_by(email=email).first()
    if existing:
        return existing.id

    user = User(
        email=email,
        auth_provider="email",
        subscription_plan=PLAN_MAP.get(plan, SubscriptionPlan.FREE),
        subscription_status=SubscriptionStatus.ACTIVE,
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        password_hash=_hash_password("Password1!"),
        agreed_to_terms=True,
        onboarding_completed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.id


def _create_session_with_message(db, user_id):
    """建立一個 ai_chat_session + 一則 AI 訊息，回傳 (session, message)。"""
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
        content="這是 AI 教練的回應，幫助你理解概念。",
    )
    db.add(message)
    db.commit()
    db.refresh(session)
    db.refresh(message)
    return session, message


@given('已存在 FREE 用戶 "{email}"')
def step_create_free_user(context, email):
    db = context.db_session
    if not hasattr(context, "ids"):
        context.ids = {}
    if not hasattr(context, "memo"):
        context.memo = {}
    user_id = _ensure_user(db, email, plan="FREE")
    context.ids[email] = str(user_id)


@given('alice 有一個 ai_chat_session 且包含一則 AI 訊息')
def step_alice_has_session_with_message(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    session, message = _create_session_with_message(db, user_id)
    context.memo["session_id"] = str(session.id)
    context.memo["message_id"] = str(message.id)
    context.memo["alice_session_id"] = str(session.id)


@given('alice 已在該 session 建立 5 筆 annotations')
def step_alice_has_5_annotations(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    session_id = uuid.UUID(context.memo["session_id"])
    message_id = uuid.UUID(context.memo["message_id"])

    for i in range(5):
        ann = ChatMessageAnnotation(
            message_id=message_id,
            user_id=user_id,
            session_id=session_id,
            highlighted_text=f"片段 {i+1}",
            user_annotation=f"這是第 {i+1} 筆評語，必須達到最少十個字元",
            annotation_type="note",
        )
        db.add(ann)
    db.commit()


@given('alice 有兩個 ai_chat_session 各含一則 AI 訊息')
def step_alice_has_two_sessions(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])

    session1, message1 = _create_session_with_message(db, user_id)
    session2, message2 = _create_session_with_message(db, user_id)

    context.memo["session_1_id"] = str(session1.id)
    context.memo["message_1_id"] = str(message1.id)
    context.memo["session_2_id"] = str(session2.id)
    context.memo["message_2_id"] = str(message2.id)


@given('alice 在 session_1 建立 2 筆 annotations')
def step_alice_2_annotations_session1(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    session_id = uuid.UUID(context.memo["session_1_id"])
    message_id = uuid.UUID(context.memo["message_1_id"])

    for i in range(2):
        ann = ChatMessageAnnotation(
            message_id=message_id,
            user_id=user_id,
            session_id=session_id,
            highlighted_text=f"session1 片段 {i+1}",
            user_annotation=f"這是 session1 第 {i+1} 筆評語，字數要夠多才行",
            annotation_type="note",
        )
        db.add(ann)
    db.commit()


@given('alice 在 session_2 建立 1 筆 annotation')
def step_alice_1_annotation_session2(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    session_id = uuid.UUID(context.memo["session_2_id"])
    message_id = uuid.UUID(context.memo["message_2_id"])

    ann = ChatMessageAnnotation(
        message_id=message_id,
        user_id=user_id,
        session_id=session_id,
        highlighted_text="session2 片段 1",
        user_annotation="這是 session2 第一筆評語，字數要夠多才行",
        annotation_type="key_insight",
    )
    db.add(ann)
    db.commit()


@given('alice 已建立一筆 annotation')
def step_alice_has_one_annotation(context):
    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    session_id = uuid.UUID(context.memo["session_id"])
    message_id = uuid.UUID(context.memo["message_id"])

    ann = ChatMessageAnnotation(
        message_id=message_id,
        user_id=user_id,
        session_id=session_id,
        highlighted_text="重要片段",
        user_annotation="這是一筆測試評語，用來測試刪除功能是否正確",
        annotation_type="note",
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)
    context.memo["annotation_id"] = str(ann.id)
    context.memo["alice_annotation_id"] = str(ann.id)
