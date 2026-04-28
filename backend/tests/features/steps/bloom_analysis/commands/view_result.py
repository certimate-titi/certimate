"""When 使用者查看測驗結果 — Bloom 分析參數無感版本

對應 Feature 18 「測驗結果頁顯示各 Bloom 層次的答對率」 Scenario，
規格僅寫 `When 使用者查看測驗結果`（無 email/exam_id 參數），
依靠 `bloom_analysis/aggregate_given/exam_completed.py` 寫入 context.memo
的 `current_user_email` + `current_exam_id` 取得當前使用者與測驗。
"""

import uuid

from behave import when


@when('使用者查看測驗結果')
def step_impl(context):
    email = context.memo.get("current_user_email") or context.memo.get(
        "completed_exam_email"
    )
    exam_id = context.memo.get("current_exam_id") or context.memo.get(
        "completed_exam_id"
    )
    assert email and exam_id, (
        "需先在 Given 透過 exam_completed.py 設定 current_user_email/current_exam_id"
    )

    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    # exam_id 在 memo 內已是 UUID 字串
    response = context.api_client.get(
        f"/api/v1/exams/{exam_id}/result",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
