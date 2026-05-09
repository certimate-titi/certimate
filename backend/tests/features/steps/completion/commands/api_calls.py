"""Completion Framework — When (API call) steps."""

import uuid

from behave import when


def _auth_header(context, email: str) -> dict:
    user_id = uuid.UUID(context.ids[email])
    token = context.jwt_helper.generate_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _resolve_subject_id(context, subject_name_or_uuid: str) -> str:
    """若傳入科目名稱則從 context.ids 轉換，否則直接當 UUID。

    查找順序：completion_subject_* → subject_* → 原字串（UUID）
    """
    # 先找 completion_subject_{name}（本模組慣用 key）
    key1 = f"completion_subject_{subject_name_or_uuid}"
    if key1 in context.ids:
        return context.ids[key1]
    # 再找 subject_{name}（其他模組慣用 key）
    key2 = f"subject_{subject_name_or_uuid}"
    if key2 in context.ids:
        return context.ids[key2]
    # 若非名稱，直接當 UUID 字串
    return subject_name_or_uuid


@when('使用者 "{email}" 查詢科目 "{subject}" 完成度')
def step_get_completion(context, email, subject):
    sid = _resolve_subject_id(context, subject)
    context.last_response = context.api_client.get(
        f"/api/v1/subjects/{sid}/completion",
        headers=_auth_header(context, email),
    )


@when('未認證使用者查詢科目 "{subject}" 完成度')
def step_get_completion_unauth(context, subject):
    sid = _resolve_subject_id(context, subject)
    context.last_response = context.api_client.get(
        f"/api/v1/subjects/{sid}/completion"
    )
