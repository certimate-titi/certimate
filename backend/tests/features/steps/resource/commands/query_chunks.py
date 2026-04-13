"""When 使用者查詢資源分塊。"""

import uuid

from behave import when


@when('使用者 "{email}" 查詢資源分塊')
def step_query_own_chunks(context, email):
    """查詢 memo 中 last_resource_id 的分塊。"""
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    resource_id = context.memo.get("last_resource_id")
    assert resource_id is not None, "找不到 last_resource_id"

    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.get(
        f"/api/v1/resources/{resource_id}/chunks",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 查詢 seed 資源分塊')
def step_query_seed_chunks(context, email):
    """查詢 memo 中 seed_resource_id 的分塊。"""
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    resource_id = context.memo.get("seed_resource_id")
    assert resource_id is not None, "找不到 seed_resource_id"

    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.get(
        f"/api/v1/resources/{resource_id}/chunks",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 查詢該資源的分塊')
def step_query_other_chunks(context, email):
    """查詢 memo 中 last_resource_id 的分塊（用於他人資源場景）。"""
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    resource_id = context.memo.get("last_resource_id")
    assert resource_id is not None, "找不到 last_resource_id"

    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.get(
        f"/api/v1/resources/{resource_id}/chunks",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 查詢不存在的資源分塊')
def step_query_nonexistent_chunks(context, email):
    """查詢一個不存在的 resource_id。"""
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    fake_id = str(uuid.uuid4())
    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.get(
        f"/api/v1/resources/{fake_id}/chunks",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
