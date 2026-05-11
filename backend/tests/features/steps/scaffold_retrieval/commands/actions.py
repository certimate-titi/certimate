"""When step actions — Feature 37 BDD."""

import uuid

from behave import when


def _auth_headers_for(context, email):
    if not hasattr(context, "ids"):
        context.ids = {}
    if email not in context.ids:
        from tests.features.steps.scaffold_retrieval.aggregate_given.setup import (
            _ensure_user,
        )
        context.ids[email] = str(_ensure_user(context.db_session, email))
        context.db_session.commit()
    token = context.jwt_helper.generate_token(uuid.UUID(context.ids[email]))
    return {"Authorization": f"Bearer {token}"}


def _resource_id_for(context, res_name):
    res = context.memo.get("resources", {}).get(res_name)
    if res is not None:
        return str(res.id)
    return res_name  # fallback as-is（讓 endpoint 回 404）


def _scaffold_id_for(context, label):
    """取 alias UUID；若無別名則自動建立 scaffold（替 Scenario Outline 提供 sf-1）。"""
    aliases = context.memo.get("scaffold_aliases", {})
    if label in aliases:
        return str(aliases[label])
    # 自動建立：需先確認 resource 存在
    from tests.features.steps.scaffold_retrieval.aggregate_given.setup import (
        step_takeaway_with_label, step_user_has_resource_with_status,
    )
    db = context.db_session
    if not context.memo.get("resources"):
        step_user_has_resource_with_status(
            context, "alice@example.com", "res-37", "success",
        )
    step_takeaway_with_label(context, "res-37", label)
    db.commit()
    return str(context.memo["scaffold_aliases"][label])


@when('用戶 "{email}" 取得資源 "{res_name}" 的 /parsed')
def step_get_parsed(context, email, res_name):
    rid = _resource_id_for(context, res_name)
    resp = context.api_client.get(
        f"/api/v1/resources/{rid}/parsed",
        headers=_auth_headers_for(context, email),
    )
    context.last_response = resp


@when('用戶 "{email}" POST /resource-scaffolds/{label}/interactions {body}')
def step_post_interactions_named(context, email, label, body):
    import json
    sf_id = _scaffold_id_for(context, label)
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        raise AssertionError(
            f"無法解析 body JSON：{body!r} → {e}"
        ) from e
    resp = context.api_client.post(
        f"/api/v1/resource-scaffolds/{sf_id}/interactions",
        json=payload,
        headers=_auth_headers_for(context, email),
    )
    context.last_response = resp


@when('用戶 POST /resource-scaffolds/{label}/interactions {body}')
def step_post_interactions_default(context, label, body):
    """無 email 版本（用 Background 的 alice）。"""
    step_post_interactions_named(context, "alice@example.com", label, body)


@when('用戶 "{email}" GET /resources/{res_name}/chapter-practice?chapter_heading={chapter}')
def step_get_chapter_practice(context, email, res_name, chapter):
    rid = _resource_id_for(context, res_name)
    # URL-encoded '+' 在 spec 裡代表空格
    chapter_decoded = chapter.replace("+", " ")
    resp = context.api_client.get(
        f"/api/v1/resources/{rid}/chapter-practice",
        params={"chapter_heading": chapter_decoded},
        headers=_auth_headers_for(context, email),
    )
    context.last_response = resp
