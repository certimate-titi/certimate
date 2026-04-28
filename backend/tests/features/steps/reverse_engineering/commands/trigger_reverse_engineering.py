"""When 管理員/使用者對考科執行考綱逆向工程 — Command (POST)"""

import uuid

from behave import when


@when('管理員 "{email}" 對考科 "{subject_name}" 執行考綱逆向工程')
def step_impl(context, email, subject_name):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    subject_id = context.ids.get(f"subject_name_{subject_name}")
    if not subject_id:
        raise KeyError(f"找不到考科 '{subject_name}'")

    response = context.api_client.post(
        f"/api/v1/reverse-engineering/subjects/{subject_id}/trigger",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 對考科 "{subject_name}" 執行考綱逆向工程')
def step_impl_user(context, email, subject_name):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    subject_id = context.ids.get(f"subject_name_{subject_name}")
    if not subject_id:
        raise KeyError(f"找不到考科 '{subject_name}'")

    response = context.api_client.post(
        f"/api/v1/reverse-engineering/subjects/{subject_id}/trigger",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


# Spec 26 §設計變更（2026-04-28 B 路徑）— admin override 採用「透過 API」措辭
@when('管理員 "{email}" 透過 API 對考科 "{subject_name}" 執行考綱逆向工程')
def step_admin_via_api(context, email, subject_name):
    step_impl(context, email, subject_name)


@when('使用者 "{email}" 透過 API 對考科 "{subject_name}" 執行考綱逆向工程')
def step_user_via_api(context, email, subject_name):
    step_impl_user(context, email, subject_name)
