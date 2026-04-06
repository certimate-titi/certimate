"""When 查詢學習軌跡 — Query"""

from behave import when


@when('使用者 "{email}" 查詢本次練習的學習軌跡')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    subject_id = None
    for key, val in context.ids.items():
        if key.startswith("subject_name_"):
            subject_id = val
            break

    response = context.api_client.get(
        f"/api/v1/difficulty-progression/subjects/{subject_id}/trail",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 查詢錯題地圖')
def step_impl_map(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    subject_id = None
    for key, val in context.ids.items():
        if key.startswith("subject_name_"):
            subject_id = val
            break

    response = context.api_client.get(
        f"/api/v1/wrong-answer-map/subjects/{subject_id}/map",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
