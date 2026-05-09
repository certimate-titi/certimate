"""When — orphan scaffold API 呼叫（commands）.

HTTP 呼叫：
- GET  /api/v1/scaffolds/orphan-fill/{node_id}
- POST /api/v1/scaffolds/{scaffold_id}/report-inaccurate
- GET  /api/v1/admin/orphan-scaffolds/review-queue
"""

from __future__ import annotations

import uuid

from behave import when

from app.services.orphan_scaffold_fill_service import OrphanScaffoldFillService


@when('學生 "{email}" 請求節點 "{node_name}" 的 orphan scaffold')
def step_request_orphan_scaffold(context, email, node_name):
    user_id = context.ids[email]
    node_id = context.ids.get(f"node_{node_name}")
    if not node_id:
        raise AssertionError(f"找不到節點 '{node_name}' 的 ID，請先建立節點")

    token = context.jwt_helper.generate_token(user_id)
    context.last_response = context.api_client.get(
        f"/api/v1/scaffolds/orphan-fill/{node_id}",
        headers={"Authorization": f"Bearer {token}"},
    )


@when('學生 "{email}" 回報鷹架 "{reason_code}" 原因不準確')
def step_report_inaccurate(context, email, reason_code):
    user_id = context.ids[email]
    scaffold_id = context.ids.get("current_scaffold_id")
    if not scaffold_id:
        raise AssertionError("找不到 current_scaffold_id，請先建立 AI 鷹架")

    token = context.jwt_helper.generate_token(user_id)
    context.last_response = context.api_client.post(
        f"/api/v1/scaffolds/{scaffold_id}/report-inaccurate",
        json={"reason_code": reason_code, "note": "BDD 測試回報"},
        headers={"Authorization": f"Bearer {token}"},
    )


@when('學生 "{email}" 再次回報同一鷹架')
def step_report_again(context, email):
    user_id = context.ids[email]
    scaffold_id = context.ids.get("current_scaffold_id")
    if not scaffold_id:
        raise AssertionError("找不到 current_scaffold_id")

    token = context.jwt_helper.generate_token(user_id)
    context.last_response = context.api_client.post(
        f"/api/v1/scaffolds/{scaffold_id}/report-inaccurate",
        json={"reason_code": "other", "note": "再次回報"},
        headers={"Authorization": f"Bearer {token}"},
    )


@when('管理員查詢 orphan scaffold 審核佇列')
def step_admin_query_review_queue(context):
    # 找管理員 email
    admin_email = next(
        (e for e in context.ids if "admin" in e and "@" in e), None
    )
    if not admin_email:
        raise AssertionError("找不到管理員帳號，請先建立 admin@test.com")

    user_id = context.ids[admin_email]
    token = context.jwt_helper.generate_token(user_id)
    context.last_response = context.api_client.get(
        "/api/v1/admin/orphan-scaffolds/review-queue",
        headers={"Authorization": f"Bearer {token}"},
    )


@when('學生 "{email}" 查詢 orphan scaffold 審核佇列')
def step_student_query_review_queue(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    context.last_response = context.api_client.get(
        "/api/v1/admin/orphan-scaffolds/review-queue",
        headers={"Authorization": f"Bearer {token}"},
    )


@when('計算信心分數：evidence_count={evidence_count:d}，exact_hit_ratio={exact_hit_ratio:f}，distance_decay={distance_decay:f}')
def step_compute_confidence(context, evidence_count, exact_hit_ratio, distance_decay):
    """直接呼叫 service 靜態方法計算信心分數（不呼叫 HTTP API）."""
    result = OrphanScaffoldFillService.compute_confidence(
        evidence_count=evidence_count,
        exact_hit_ratio=exact_hit_ratio,
        distance_decay=distance_decay,
    )
    context.memo["confidence_score"] = result
