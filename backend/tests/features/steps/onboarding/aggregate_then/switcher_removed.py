"""Then 儀表板科目切換器不再顯示科目 — ReadModel Then (via API)"""

from behave import then


@then('儀表板科目切換器不再顯示 "{subject}"')
def step_impl(context, subject):
    email = context.memo.get("current_email")
    if not email:
        for key in context.ids:
            if "@" in key:
                email = key
                break
    user_id = context.ids.get(email)
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"
    data = response.json()
    switcher = [s.get("name") for s in data.get("subjects", [])]
    assert subject not in switcher, \
        f"科目切換器不應包含 '{subject}'，實際: {switcher}"
