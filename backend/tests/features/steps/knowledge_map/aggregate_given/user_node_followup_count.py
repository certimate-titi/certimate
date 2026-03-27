"""Given 使用者已在節點追問 N 次 — Aggregate Given"""

import uuid

from behave import given

from app.models.ai_chat import AiChatSession, AiChatMessage
from app.repositories.ai_chat_repository import AiChatSessionRepository, AiChatMessageRepository


@given('使用者 "{email}" 已在節點 {node_id:d} 追問 {count:d} 次')
def step_impl(context, email, node_id, count):
    db = context.db_session
    session_repo = AiChatSessionRepository(db)
    message_repo = AiChatMessageRepository(db)

    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    user_id = uuid.UUID(context.ids[email])
    node_uuid = uuid.UUID(int=node_id)

    # 建立 AI 對話 session
    chat_session = AiChatSession(
        user_id=user_id,
        context_type='node',
        context_id=node_uuid,
        message_count=count * 2,  # 每次追問包含 user + assistant
    )
    chat_session = session_repo.save(chat_session)

    # 建立對應數量的訊息
    for i in range(count):
        user_msg = AiChatMessage(
            session_id=chat_session.id,
            role='user',
            content=f'追問 {i + 1}',
        )
        message_repo.save(user_msg)

        assistant_msg = AiChatMessage(
            session_id=chat_session.id,
            role='assistant',
            content=f'回覆 {i + 1}',
        )
        message_repo.save(assistant_msg)
