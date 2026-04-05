"""When 使用者移除備考科目並確認 — Command (DELETE + POST confirm)"""

import uuid

from behave import when

from app.models.subject import Subject


@when('使用者 "{email}" 移除備考科目 "{subject_name}" 並確認')
def step_impl(context, email, subject_name):
    db = context.db_session
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    subject = db.query(Subject).filter_by(name=subject_name).first()
    assert subject is not None, f"找不到科目 '{subject_name}'"
    subject_id = str(subject.id)

    # Step 1: DELETE request
    response = context.api_client.delete(
        f"/api/v1/subjects/{subject_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, \
        f"移除請求失敗: {response.status_code} {response.text}"

    # Step 2: Confirm removal
    response = context.api_client.post(
        f"/api/v1/subjects/{subject_id}/confirm-remove",
        headers={"Authorization": f"Bearer {token}"},
        json={"confirmed": True},
    )
    context.last_response = response
