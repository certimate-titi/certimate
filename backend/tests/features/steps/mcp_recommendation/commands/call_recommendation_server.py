"""
MCP Recommendation Server 調用步驟
"""

from behave import when
from app.mcp.recommendation_server import RecommendationServer
import json


@when('MCP Recommendation Server 為 "{email}" 推薦 {count:d} 道題目')
def step_recommend_questions(context, email, count):
    """調用 Recommendation Server 的 RecommendQuestions 函數"""
    user_id = context.ids.get(email)
    if not user_id:
        context.last_response = {"error": True, "message": f"User {email} not found"}
        return

    server = RecommendationServer(context.db_session)
    response = server.recommend_questions(user_id, count)

    context.last_response = response


@when('MCP Recommendation Server 計算 "{email}" 題目 "{question_id}" 的複習時間')
def step_calculate_spacing(context, email, question_id):
    """調用 Recommendation Server 的 CalculateOptimalSpacing 函數"""
    user_id = context.ids.get(email)
    if not user_id:
        context.last_response = {"error": True, "message": f"User {email} not found"}
        return

    # 如果 question_id 不是 UUID，嘗試從 memo 中查找
    actual_question_id = context.memo.get(f"question_{question_id}", question_id)

    server = RecommendationServer(context.db_session)
    response = server.calculate_optimal_spacing(user_id, actual_question_id)

    context.last_response = response
    context.memo["last_spacing_response"] = response


@when('MCP Recommendation Server 為 "{email}" 建議學習 "{topic}" 的路徑')
def step_suggest_learning_path(context, email, topic):
    """調用 Recommendation Server 的 SuggestLearningPath 函數"""
    user_id = context.ids.get(email)
    if not user_id:
        context.last_response = {"error": True, "message": f"User {email} not found"}
        return

    server = RecommendationServer(context.db_session)
    response = server.suggest_learning_path(user_id, topic)

    context.last_response = response


@when('MCP Recommendation Server 驗證該節點質量')
def step_validate_node_quality(context):
    """調用 Recommendation Server 的 ValidateKnowledgeNodeQuality 函數"""
    node_data = context.memo.get("node_data", {})

    server = RecommendationServer(context.db_session)
    response = server.validate_knowledge_node_quality(node_data)

    context.last_response = response
