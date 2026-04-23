"""Canvas BDD — Command (When) API calls."""

import uuid

from behave import when


@when('使用者 "{email}" 呼叫 Canvas tier1 GET /api/v1/subjects/{subject_num:d}/canvas')
def step_call_tier1(context, email, subject_num):
    user_id = uuid.UUID(context.ids[email])
    token = context.jwt_helper.generate_token(user_id)
    subject_id = str(uuid.UUID(int=subject_num))

    context.last_response = context.api_client.get(
        f"/api/v1/subjects/{subject_id}/canvas",
        headers={"Authorization": f"Bearer {token}"},
    )


@when('使用者 "{email}" 呼叫 Canvas children GET /api/v1/subjects/{subject_num:d}/canvas/children/{parent_num:d}')
def step_call_children(context, email, subject_num, parent_num):
    user_id = uuid.UUID(context.ids[email])
    token = context.jwt_helper.generate_token(user_id)
    subject_id = str(uuid.UUID(int=subject_num))
    parent_id = str(uuid.UUID(int=parent_num))

    context.last_response = context.api_client.get(
        f"/api/v1/subjects/{subject_id}/canvas/children/{parent_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
