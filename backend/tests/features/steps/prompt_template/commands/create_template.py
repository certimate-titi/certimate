"""When: 新增 Prompt 模板。"""

import json
from behave import when


def _parse_table_to_dict(table):
    data = {}
    for row in table:
        key = row["欄位"]
        val = row["值"]
        data[key] = val
    return data


@when('使用者 "{email}" 新增 Prompt 模板：')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    data = _parse_table_to_dict(context.table)

    # 型別轉換
    if "max_tokens" in data and data["max_tokens"]:
        data["max_tokens"] = int(data["max_tokens"])
    if "temperature" in data and data["temperature"]:
        data["temperature"] = float(data["temperature"])
    if "max_tokens_by_plan" in data and isinstance(data["max_tokens_by_plan"], str):
        try:
            data["max_tokens_by_plan"] = json.loads(data["max_tokens_by_plan"])
        except (json.JSONDecodeError, ValueError):
            pass

    # 去除空字串（視為未提供）
    cleaned = {k: v for k, v in data.items() if v != ""}

    response = context.api_client.post(
        "/api/v1/admin/prompt-templates",
        json=cleaned,
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response

    if response.status_code == 200:
        tid = cleaned.get("template_id")
        if tid:
            context.memo[f"pt_{tid}_template_id"] = tid
