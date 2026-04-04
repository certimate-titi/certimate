"""When 使用者提交測驗設定（含自訂 Bloom 比例 table）— Command"""

import uuid

from behave import when, use_step_matcher

use_step_matcher("re")


@when('使用者 "(?P<email>[^"]+)" 提交測驗設定，選擇節點 (?P<node_id>\\d+)，題數為 (?P<count>\\d+)，自訂 Bloom 比例為：')
def step_impl(context, email, node_id, count):
    node_id = int(node_id)
    count = int(count)

    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    node_uuid = str(uuid.UUID(int=node_id))

    # Parse Bloom distribution from table
    bloom_distribution = {}
    for row in context.table:
        bloom_distribution[row["bloom_category"]] = int(row["percentage"])

    response = context.api_client.post(
        "/api/v1/exams/config",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "node_ids": [node_uuid],
            "question_count": count,
            "custom_bloom_ratio": bloom_distribution,
        },
    )
    context.last_response = response

    # Store bloom distribution in memo for later verification
    context.memo["submitted_bloom_distribution"] = bloom_distribution


use_step_matcher("parse")
