"""When 使用者切換已選科目的自評程度 — Command"""

from behave import when


@when('使用者將 "{subject}" 的自評程度切換為 "{level}"')
def step_impl(context, subject, level):
    """呼叫 API 更新科目自評程度。"""
    token = context.memo.get("current_token")
    response = context.api_client.patch(
        "/api/v1/onboarding/subjects/level",
        json={"subject_name": subject, "self_assessed_level": level},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["last_subject_level_update"] = {"subject": subject, "level": level}
