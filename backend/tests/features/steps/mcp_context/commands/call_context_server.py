"""
MCP Context Server 調用步驟
"""

from behave import when
from app.mcp.context_server import ContextServer


@when('MCP Context Server 構建 "{email}" 的學習上下文')
def step_build_user_context(context, email):
    """調用 MCP Context Server 的 BuildContextForCoach 函數"""
    # 從 context.ids 中獲取 user_id
    user_id = context.ids.get(email)
    if not user_id:
        context.last_response = {"error": True, "message": f"User {email} not found in context"}
        return

    # 初始化 Context Server
    server = ContextServer(context.db_session)

    # 呼叫 build_context_for_coach
    response = server.build_context_for_coach(user_id)

    context.last_response = response
    context.memo["last_user_id"] = user_id


@when('MCP Context Server 獲取 "{email}" 在 "{topic}" 的弱點詳情')
def step_fetch_weak_area_details(context, email, topic):
    """調用 MCP Context Server 的 FetchWeakAreaDetails 函數"""
    user_id = context.ids.get(email)
    if not user_id:
        context.last_response = {"error": True, "message": f"User {email} not found"}
        return

    server = ContextServer(context.db_session)
    response = server.fetch_weak_area_details(user_id, topic)

    context.last_response = response
    context.memo["last_topic"] = topic


@when('MCP Context Server 獲取 "{email}" 的學習風格')
def step_get_learning_style(context, email):
    """調用 MCP Context Server 的 GetUserLearningStyle 函數"""
    user_id = context.ids.get(email)
    if not user_id:
        context.last_response = {"error": True, "message": f"User {email} not found"}
        return

    server = ContextServer(context.db_session)
    response = server.get_user_learning_style(user_id)

    context.last_response = response


@when('MCP Context Server 獲取 "{email}" 最近 {limit:d} 筆錯誤')
def step_fetch_recent_errors(context, email, limit):
    """調用 MCP Context Server 的 FetchRecentErrors 函數"""
    user_id = context.ids.get(email)
    if not user_id:
        context.last_response = {"error": True, "message": f"User {email} not found"}
        return

    server = ContextServer(context.db_session)
    response = server.fetch_recent_errors(user_id, limit)

    context.last_response = response
