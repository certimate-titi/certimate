from behave import when


@when('使用者 "{email}" 提交 YouTube URL "{url}"，科目為 {subject_id:d}')
def step_impl(context, email, url, subject_id):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    token = context.jwt_helper.generate_token(user_id)
    subject_uuid = context.ids.get(f"subject_{subject_id}")

    response = context.api_client.post(
        "/api/v1/resources/youtube",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "youtube_url": url,
            "subject_id": subject_uuid,
        },
    )
    context.last_response = response
