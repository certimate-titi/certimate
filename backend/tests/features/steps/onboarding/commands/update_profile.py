"""When 使用者修改以下欄位並點擊「儲存變更」— Command (PUT)"""

from behave import when


FIELD_MAP = {
    "姓名": "display_name",
    "年齡": "age",
    "最高學歷": "education",
    "職業 / 領域": "career",
    "每日學習時間": "daily_study_minutes",
    "偏好學習方式": "learning_style",
}


@when('使用者修改以下欄位並點擊「儲存變更」：')
def step_impl(context):
    token = context.memo.get("current_token")

    payload = {}
    for row in context.table:
        field_label = row["欄位"]
        value = row["新值"]
        api_key = FIELD_MAP.get(field_label, field_label)
        # Convert numeric fields
        if api_key in ("age", "daily_study_minutes"):
            import re
            nums = re.findall(r'\d+', value)
            value = int(nums[0]) if nums else value
        payload[api_key] = value

    response = context.api_client.patch(
        "/api/v1/dashboard/profile",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    context.last_response = response
