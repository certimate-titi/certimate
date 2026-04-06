"""When 使用者查詢錯題地圖 — Query"""

from behave import when


@when('使用者 "{email}" 查詢考科 "{subject_name}" 的錯題地圖')
def step_impl(context, email, subject_name):
    user_id = context.ids[email]
    subject_id = context.ids.get(f"subject_name_{subject_name}")
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        f"/api/v1/wrong-answer-map/subjects/{subject_id}/map",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 查詢考科 "{subject_name}" 的錯題地圖，時間範圍為 "{time_range}"')
def step_impl_with_time(context, email, subject_name, time_range):
    user_id = context.ids[email]
    subject_id = context.ids.get(f"subject_name_{subject_name}")
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        f"/api/v1/wrong-answer-map/subjects/{subject_id}/map",
        headers={"Authorization": f"Bearer {token}"},
        params={"time_range": time_range},
    )
    context.last_response = response
