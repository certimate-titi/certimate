"""Coverage retrofit — minimal When/Then bindings for Feature 35 (ISS-015).

Goal: smoke-call 14 endpoints to prove they exist (not 404). Status assertion
is permissive (multiple acceptable codes per scenario).
"""
import io
import re
import uuid

from behave import when, then


def _auth(context, email):
    user_id = uuid.UUID(context.ids[email])
    return {"Authorization": f"Bearer {context.jwt_helper.generate_token(user_id)}"}


# ───────── Admin Dashboard ─────────

@when('使用者 "{email}" 查詢系統負載指標')
def step_system_load(context, email):
    context.last_response = context.api_client.get(
        "/api/v1/admin/dashboard/system-load", headers=_auth(context, email)
    )


# ───────── B2B / DPA / 學生管理 ─────────

@when('使用者 "{email}" 查詢 DPA 狀態')
def step_get_dpa(context, email):
    context.last_response = context.api_client.get(
        "/api/v1/b2b/dpa", headers=_auth(context, email)
    )


@when('使用者 "{email}" 簽署 DPA')
def step_sign_dpa(context, email):
    context.last_response = context.api_client.post(
        "/api/v1/b2b/dpa/sign", json={"signer_name": "test"}, headers=_auth(context, email)
    )


@when('使用者 "{email}" 刪除學生 "{student_id}"')
def step_delete_student(context, email, student_id):
    context.last_response = context.api_client.delete(
        f"/api/v1/b2b/students/{student_id}", headers=_auth(context, email)
    )


@when('使用者 "{email}" 查詢班級 "{group_id}" 弱點分析')
def step_class_weakness(context, email, group_id):
    context.last_response = context.api_client.get(
        f"/api/v1/b2b/class/{group_id}/weakness", headers=_auth(context, email)
    )


# ───────── Dashboard ─────────

@when('使用者 "{email}" 查詢成就列表')
def step_achievements(context, email):
    context.last_response = context.api_client.get(
        "/api/v1/dashboard/achievements", headers=_auth(context, email)
    )


@when('使用者 "{email}" 查詢儀表板使用量')
def step_dashboard_usage(context, email):
    context.last_response = context.api_client.get(
        "/api/v1/dashboard/usage", headers=_auth(context, email)
    )


@when('使用者 "{email}" 匯出儀表板資料')
def step_dashboard_export(context, email):
    context.last_response = context.api_client.get(
        "/api/v1/dashboard/export", headers=_auth(context, email)
    )


@when('使用者 "{email}" 上傳頭像')
def step_upload_avatar(context, email):
    files = {"file": ("avatar.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")}
    context.last_response = context.api_client.post(
        "/api/v1/dashboard/profile/avatar", files=files, headers=_auth(context, email)
    )


@when('使用者 "{email}" 完成每日任務 "{quest_id}"')
def step_complete_quest(context, email, quest_id):
    context.last_response = context.api_client.post(
        f"/api/v1/dashboard/quests/{quest_id}/complete", headers=_auth(context, email)
    )


# ───────── Exam Draft / Settlement ─────────

@when('使用者 "{email}" 讀取考試 "{exam_id}" 草稿')
def step_get_exam_draft(context, email, exam_id):
    context.last_response = context.api_client.get(
        f"/api/v1/exams/{exam_id}/draft", headers=_auth(context, email)
    )


@when('使用者 "{email}" 查詢考試 "{exam_id}" 結算狀態')
def step_settlement_status(context, email, exam_id):
    context.last_response = context.api_client.get(
        f"/api/v1/exams/{exam_id}/settlement-status", headers=_auth(context, email)
    )


# ───────── Knowledge Map ─────────

@when('使用者 "{email}" 對節點 "{node_id}" 發起教練對話')
def step_node_chat(context, email, node_id):
    context.last_response = context.api_client.post(
        f"/api/v1/knowledge-map/nodes/{node_id}/chat",
        json={"message": "smoke"},
        headers=_auth(context, email),
    )


@when('使用者 "{email}" 查詢資源 "{resource_id}" 摘要')
def step_resource_summary(context, email, resource_id):
    context.last_response = context.api_client.get(
        f"/api/v1/knowledge-map/resources/{resource_id}/summary",
        headers=_auth(context, email),
    )


# ───────── Permissive status assertion ─────────
# Feature 35 only verifies endpoint exists (not 404) — accepts a list of
# acceptable codes joined by 「或」.

_STATUS_RE = re.compile(r"\d+")


@then('回應狀態應為 {codes}')
def step_status_in(context, codes):
    expected = {int(c) for c in _STATUS_RE.findall(codes)}
    actual = context.last_response.status_code
    assert actual in expected, (
        f"Expected status in {sorted(expected)}, got {actual}. "
        f"Body: {context.last_response.text[:200]}"
    )
