"""When — PRD-034 Fork HTTP API 呼叫。"""

from __future__ import annotations

import uuid

from behave import when


def _auth_headers(context, email: str | None = None):
    if email and email in context.ids:
        token = context.jwt_helper.generate_token(context.ids[email])
    else:
        token = context.memo.get("current_token")
    return {"Authorization": f"Bearer {token}"}


@when('我呼叫 POST "/api/v1/subjects/{{platform_subject_id}}/fork-from-platform"')
@when('我再次呼叫 POST "/api/v1/subjects/{{platform_subject_id}}/fork-from-platform"')
def step_fork(context):
    pid = context.memo["platform_subject_id"]
    context.last_response = context.api_client.post(
        f"/api/v1/subjects/{pid}/fork-from-platform",
        headers=_auth_headers(context),
    )


@when('我呼叫 DELETE "/api/v1/resources/{{{res}_id}}"')
def step_delete_resource(context, res):
    rid = context.memo[f"{res}_id"]
    context.last_response = context.api_client.delete(
        f"/api/v1/resources/{rid}",
        headers=_auth_headers(context),
    )


@when('我呼叫 GET "/api/v1/knowledge-map/subjects/{{user_subject_id}}/nodes"')
def step_get_nodes(context):
    sid = context.memo["user_subject_id"]
    context.last_response = context.api_client.get(
        f"/api/v1/knowledge-map/subjects/{sid}/nodes",
        headers=_auth_headers(context),
    )


@when('我呼叫 PUT "/api/v1/admin/platform-subjects/{{id}}/draft" 修改資源清單')
def step_put_draft(context):
    pid = context.memo["platform_subject_id"]
    # 用一份新的 UUID 清單（可能不存在的 resource），僅測端點接受
    new_ids = [str(uuid.uuid4())]
    # 建立臨時 resource 讓 FK 成立
    from app.models.resource import Resource, ResourceScope, ResourceStatus, ResourceType
    from app.models.user import User

    db = context.db_session
    admin = db.query(User).filter(User.role == "admin").first()
    tmp_rid = uuid.UUID(new_ids[0])
    db.add(
        Resource(
            id=tmp_rid,
            user_id=admin.id,
            subject_id=uuid.UUID(pid),
            name="draft.pdf",
            type=ResourceType.PDF.value,
            scope=ResourceScope.PLATFORM.value,
            status=ResourceStatus.COMPLETED.value,
            file_size_bytes=1,
            tags=None,
        )
    )
    db.commit()

    context.last_response = context.api_client.put(
        f"/api/v1/admin/platform-subjects/{pid}/draft",
        headers=_auth_headers(context),
        json={"resource_ids": new_ids},
    )


@when('我呼叫 POST "/api/v1/admin/platform-subjects/{{id}}/publish"')
def step_publish(context):
    pid = context.memo["platform_subject_id"]
    context.last_response = context.api_client.post(
        f"/api/v1/admin/platform-subjects/{pid}/publish",
        headers=_auth_headers(context),
    )


@when('我呼叫 POST "/api/v1/admin/platform-subjects/{{id}}/rollback"')
def step_rollback(context):
    pid = context.memo["platform_subject_id"]
    context.last_response = context.api_client.post(
        f"/api/v1/admin/platform-subjects/{pid}/rollback",
        headers=_auth_headers(context),
    )


@when('考生 "{email}" 接著 fork 同一 platform subject')
def step_other_user_fork(context, email):
    from app.models.user import User

    db = context.db_session
    if email not in context.ids:
        uid = uuid.uuid4()
        db.add(User(id=uid, email=email, password_hash="x", display_name=email))
        db.commit()
        context.ids[email] = str(uid)
    token = context.jwt_helper.generate_token(context.ids[email])
    pid = context.memo["platform_subject_id"]
    context.last_response = context.api_client.post(
        f"/api/v1/subjects/{pid}/fork-from-platform",
        headers={"Authorization": f"Bearer {token}"},
    )
    if context.last_response.status_code == 201:
        context.memo[f"{email}_subject_id"] = context.last_response.json()[
            "user_subject_id"
        ]
