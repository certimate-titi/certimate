"""When 使用者提交測驗設定（含難易度分配）— Command"""

import re
import uuid

from behave import when


def _parse_difficulty(difficulty_str):
    """解析難易度分配字串，如 'Easy:50% Medium:50% Hard:0%'"""
    result = {}
    parts = re.findall(r'(\w+):(\d+)%', difficulty_str)
    for level, pct in parts:
        result[level.lower()] = int(pct)
    return result


@when('使用者 "{email}" 提交測驗設定，選擇節點 {node1:d} 和節點 {node2:d}，題數為 {count:d}，難易度分配為 {difficulty}')
def step_impl(context, email, node1, node2, count, difficulty):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    diff_dist = _parse_difficulty(difficulty)

    response = context.api_client.post(
        "/api/v1/exams/config",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "node_ids": [str(uuid.UUID(int=node1)), str(uuid.UUID(int=node2))],
            "question_count": count,
            "difficulty_distribution": diff_dist,
        },
    )
    context.last_response = response
