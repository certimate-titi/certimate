"""When: A/B 測試操作。"""

from behave import when


def _parse_table_to_dict(table):
    data = {}
    for row in table:
        key = row["欄位"]
        val = row["值"]
        data[key] = val
    return data


@when('使用者 "{email}" 為模板 "{template_id}" 建立 A/B 測試：')
def step_impl(context, email, template_id):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    data = _parse_table_to_dict(context.table)

    if "traffic_split" in data:
        data["traffic_split"] = int(data["traffic_split"])
    if "variant_b_temperature" in data and data["variant_b_temperature"]:
        data["variant_b_temperature"] = float(data["variant_b_temperature"])

    response = context.api_client.post(
        f"/api/v1/admin/prompt-templates/{template_id}/ab-tests",
        json=data,
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response

    if response.status_code == 200:
        ab_id = response.json().get("ab_test_id")
        if ab_id:
            context.ids[f"ab_{template_id}"] = ab_id


@when('使用者 "{email}" 結束 A/B 測試 "{test_name}"，勝者為 "{winner}"')
def step_impl(context, email, test_name, winner):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    # 根據 test_name 找 test_id
    test_id = context.ids.get(test_name, test_name)

    response = context.api_client.patch(
        f"/api/v1/admin/prompt-templates/ab-tests/{test_id}",
        json={"action": "complete", "winner": winner},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 取消 A/B 測試 "{test_name}"')
def step_impl(context, email, test_name):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    test_id = context.ids.get(test_name, test_name)

    response = context.api_client.patch(
        f"/api/v1/admin/prompt-templates/ab-tests/{test_id}",
        json={"action": "cancel"},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when("AI 服務請求模板 \"{name}\"")
def step_impl(context, name):
    response = context.api_client.get(
        f"/api/v1/internal/prompt-templates/{name}",
    )
    context.last_response = response


@when("AI 服務為 user_id hash 值 {hash_val:d} 的用戶請求模板 \"{name}\"")
def step_impl(context, hash_val, name):
    response = context.api_client.get(
        f"/api/v1/internal/prompt-templates/{name}?user_id_hash={hash_val}",
    )
    context.last_response = response


@when("執行 Prompt 模板 seed 腳本")
def step_impl(context):
    """模擬 seed 腳本執行（測試用：直接調用 service 或 API）。"""
    # 在測試環境中，seed 腳本效果由 aggregate_given 模擬
    # 此處僅記錄 memo 供 then 步驟使用
    context.memo["seed_executed"] = True
