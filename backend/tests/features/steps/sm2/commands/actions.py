"""When step actions — Feature 42 SM-2 / today / concept-center BDD."""

import uuid

from behave import when


def _resolve_user_id(context):
    """從 context.memo / context.ids 取用 user_id，缺則建 default alice。"""
    if "last_user_id" in context.memo:
        return context.memo["last_user_id"]
    ids = getattr(context, "ids", {})
    if "alice@example.com" in ids:
        return uuid.UUID(ids["alice@example.com"])
    # Fallback：自動建 alice
    from tests.features.steps.sm2.aggregate_given.setup import _ensure_user
    db = context.db_session
    user_id = _ensure_user(db, "alice@example.com")
    db.commit()
    if not hasattr(context, "ids"):
        context.ids = {}
    context.ids["alice@example.com"] = str(user_id)
    context.memo["last_user_id"] = user_id
    return user_id


def _auth_headers(context, user_id):
    """產生 JWT Bearer header。"""
    uid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
    token = context.jwt_helper.generate_token(uid)
    return {"Authorization": f"Bearer {token}"}


@when('用戶第 {n:d} 次 quality={quality}')
def step_next_quality(context, n, quality):
    """後續複習：用 last_scaffold_id + last_user_id 直接呼叫 sm2_service。"""
    from app.services.sm2_service import update_review

    db = context.db_session
    user_id = context.memo["last_user_id"]
    scaffold_id = context.memo["last_scaffold_id"]
    sched = update_review(db, user_id, scaffold_id, quality)
    db.commit()
    context.memo["last_sched"] = sched


@when('用戶 GET /scaffold-reviews/due')
def step_get_due(context):
    user_id = _resolve_user_id(context)
    resp = context.api_client.get(
        "/api/v1/scaffold-reviews/due",
        headers=_auth_headers(context, user_id),
    )
    context.last_response = resp


@when('用戶 GET /scaffold-reviews/due?limit={limit:d}')
def step_get_due_with_limit(context, limit):
    user_id = _resolve_user_id(context)
    resp = context.api_client.get(
        f"/api/v1/scaffold-reviews/due?limit={limit}",
        headers=_auth_headers(context, user_id),
    )
    context.last_response = resp


@when('用戶 GET /dashboard/today')
def step_get_today(context):
    user_id = _resolve_user_id(context)
    resp = context.api_client.get(
        "/api/v1/dashboard/today",
        headers=_auth_headers(context, user_id),
    )
    context.last_response = resp


@when('用戶 GET /concept-center?q={q}')
def step_get_concept_center(context, q):
    user_id = _resolve_user_id(context)
    resp = context.api_client.get(
        f"/api/v1/concept-center?q={q}",
        headers=_auth_headers(context, user_id),
    )
    context.last_response = resp
