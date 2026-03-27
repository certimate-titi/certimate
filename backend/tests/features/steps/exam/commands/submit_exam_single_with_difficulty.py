"""When 使用者提交測驗設定（單節點含難易度分配）— Command"""

import re
import uuid

from behave import when


def _parse_difficulty(difficulty_str):
    result = {}
    parts = re.findall(r'(\w+):(\d+)%', difficulty_str)
    for level, pct in parts:
        result[level.lower()] = int(pct)
    return result


@when('使用者 "{email}" 提交測驗設定，選擇節點 {node_id:d}，題數為 {count:d}，難易度分配為 {difficulty}')
def step_impl(context, email, node_id, count, difficulty):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    diff_dist = _parse_difficulty(difficulty)

    response = context.api_client.post(
        "/api/v1/exams/config",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "node_ids": [str(uuid.UUID(int=node_id))],
            "question_count": count,
            "difficulty_distribution": diff_dist,
        },
    )
    context.last_response = response
