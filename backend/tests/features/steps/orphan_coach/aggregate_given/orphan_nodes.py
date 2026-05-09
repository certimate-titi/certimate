"""Orphan Coach — Given: 建立測試所需的知識節點、科目、mastery 等前提資料。"""

import uuid

from behave import given, when  # noqa: F401


@given('使用者 {email} 已認證')
def step_user_authenticated(context, email):
    """設定當前測試使用者。email 不含引號（feature 寫法）。"""
    # 去除可能的引號
    email = email.strip().strip('"').strip("'")
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID，請確認 Background Given 已建立此帳號")
    context.memo["current_user_email"] = email
    context.memo["user_id"] = str(context.ids[email])


@when('我向 {path} 發送未認證 POST 請求，body 為 {body}')
def step_unauthenticated_post(context, path, body):
    """未認證 POST 請求。"""
    import json
    try:
        body_dict = json.loads(body)
    except Exception:
        body_dict = {}
    context.last_response = context.api_client.post(path, json=body_dict)

from app.models.knowledge_node import KnowledgeNode
from app.models.subject import Subject, SubjectCategory
from app.models.node_mastery import NodeMastery
from app.models.ai_chat import AiChatSession, AiChatMessage
from app.services.orphan_coach_service import SOCRATIC_MODE


@given('科目「{subject_name}」存在')
def step_subject_exists(context, subject_name):
    cat = SubjectCategory(name="測試分類")
    context.db_session.add(cat)
    context.db_session.flush()

    subj = Subject(
        name=subject_name,
        category_id=cat.id,
    )
    context.db_session.add(subj)
    context.db_session.commit()  # commit 讓其他 session 可見
    context.memo["subject_id"] = str(subj.id)
    context.memo["subject_name"] = subject_name


@given('知識節點「{node_name}」屬於科目「{subject_name}」')
def step_node_in_subject(context, node_name, subject_name):
    subj_id = context.memo.get("subject_id")
    node = KnowledgeNode(
        name=node_name,
        subject_id=uuid.UUID(subj_id) if subj_id else None,
        depth=2,
        available_questions=5,
    )
    context.db_session.add(node)
    context.db_session.commit()  # commit 讓其他 session 可見
    context.memo["node_id"] = str(node.id)
    context.memo["node_name"] = node_name


@given('知識節點「{node_name}」存在，ID 為隨機')
def step_node_exists(context, node_name):
    node = KnowledgeNode(
        name=node_name,
        depth=2,
        available_questions=3,
    )
    context.db_session.add(node)
    context.db_session.commit()  # commit 讓其他 session 可見
    context.memo["node_id"] = str(node.id)
    context.memo["node_name"] = node_name


@given('使用者已有一個進行中的蘇格拉底對話（節點為 node_id，輪數 {rounds:d} 輪）')
def step_existing_conversation(context, rounds):
    node_id = context.memo.get("node_id")
    user_id = context.memo.get("user_id") or context.ids.get(
        next(iter(context.ids), ""), None
    )
    if not user_id or not node_id:
        raise AssertionError("需要先建立使用者與節點")

    session = AiChatSession(
        user_id=uuid.UUID(str(user_id)),
        context_type="knowledge_node",
        context_id=uuid.UUID(node_id),
        model_used="claude-haiku-4-5-20251001",
        mode=SOCRATIC_MODE,
        node_id=uuid.UUID(node_id),
        message_count=rounds * 2,
        mastery_committed=False,
    )
    context.db_session.add(session)
    context.db_session.flush()
    context.memo["conversation_id"] = str(session.id)

    # 建假訊息
    for i in range(rounds):
        ai_msg = AiChatMessage(
            session_id=session.id,
            role="assistant",
            content=f"第 {i+1} 輪 AI 問句",
        )
        context.db_session.add(ai_msg)
        user_msg = AiChatMessage(
            session_id=session.id,
            role="user",
            content=f"第 {i+1} 輪學生回覆，提及相關概念" * 2,
            score_concept=1.0,
            score_reasoning=0.5,
            score_initiative=0.5,
            round_score=2.0,
        )
        context.db_session.add(user_msg)

    context.db_session.commit()


@given('對話已暫停（paused_at 設置）')
def step_conversation_paused(context):
    from datetime import datetime, timezone
    conv_id = context.memo.get("conversation_id")
    if not conv_id:
        raise AssertionError("需要先建立對話")
    session = context.db_session.query(AiChatSession).filter(
        AiChatSession.id == uuid.UUID(conv_id)
    ).first()
    if session:
        session.paused_at = datetime.now(timezone.utc)
        context.db_session.commit()
