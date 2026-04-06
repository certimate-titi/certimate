"""When 系統計算下一題的出題策略 — Command"""

import json

from behave import when


@when('系統計算下一題的出題策略')
def step_impl(context):
    # Find current user
    email = None
    for key in context.memo:
        if key.startswith("practice_node_") and not key.startswith("practice_node_id_"):
            email = key.replace("practice_node_", "")
            break

    if not email:
        raise KeyError("找不到當前練習的使用者")

    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    subject_id = None
    for key, val in context.ids.items():
        if key.startswith("subject_name_"):
            subject_id = val
            break

    body = {
        "current_node_id": context.memo.get(f"practice_node_id_{email}"),
        "original_node_id": context.memo.get(f"original_node_id_{email}"),
        "consecutive_wrong": context.memo.get(f"consecutive_wrong_{email}", 0),
        "consecutive_correct": context.memo.get(f"consecutive_correct_{email}", 0),
    }

    response = context.api_client.post(
        f"/api/v1/difficulty-progression/subjects/{subject_id}/next-strategy",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
    )
    context.last_response = response


@when('使用者 "{email}" 請求下一題')
def step_impl_next(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    subject_id = None
    for key, val in context.ids.items():
        if key.startswith("subject_name_"):
            subject_id = val
            break

    body = {
        "current_node_id": context.memo.get(f"practice_node_id_{email}"),
        "original_node_id": context.memo.get(f"original_node_id_{email}"),
        "consecutive_wrong": context.memo.get(f"consecutive_wrong_{email}", 0),
        "consecutive_correct": context.memo.get(f"consecutive_correct_{email}", 0),
    }

    response = context.api_client.post(
        f"/api/v1/difficulty-progression/subjects/{subject_id}/next-strategy",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
    )
    context.last_response = response


@when('使用者 "{email}" 請求自適應練習')
def step_impl_request_adaptive(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    subject_id = None
    for key, val in context.ids.items():
        if key.startswith("subject_name_"):
            subject_id = val
            break

    response = context.api_client.post(
        f"/api/v1/difficulty-progression/subjects/{subject_id}/start",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
