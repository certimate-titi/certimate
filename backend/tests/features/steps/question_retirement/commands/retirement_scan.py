"""When 系統執行退場掃描 — Command"""

from behave import when


@when('系統執行每日退場掃描')
def step_impl(context):
    response = context.api_client.post(
        "/api/v1/admin/retirement/scan",
    )
    context.last_response = response


@when('系統執行每日硬刪除掃描')
def step_hard_delete_scan(context):
    response = context.api_client.post(
        "/api/v1/admin/retirement/hard-delete",
    )
    context.last_response = response


@when('系統恢復該科目的軟刪除 AI 題')
def step_restore(context):
    subject_id = context.memo.get("ai_subject_id")

    response = context.api_client.post(
        "/api/v1/ai-questions/restore",
        json={"subject_id": subject_id},
    )
    context.last_response = response


@when('系統偵測到回報次數達標')
def step_report_threshold(context):
    question_id = context.memo.get("current_question_id")

    response = context.api_client.post(
        "/api/v1/ai-questions/check-reports",
        json={"question_id": question_id},
    )
    context.last_response = response


@when('系統計算 available_questions')
def step_calc_available(context):
    response = context.api_client.post(
        "/api/v1/admin/subjects/recalculate",
    )
    context.last_response = response


@when('系統執行放榜後退場掃描')
def step_result_retirement(context):
    response = context.api_client.post(
        "/api/v1/admin/retirement/post-result",
    )
    context.last_response = response


@when('系統於凌晨 03:00 執行每日退場掃描')
def step_scheduled_scan(context):
    response = context.api_client.post(
        "/api/v1/admin/retirement/scan",
    )
    context.last_response = response


@when('系統準備執行批次軟刪除')
def step_batch_soft_delete(context):
    response = context.api_client.post(
        "/api/v1/admin/retirement/scan",
    )
    context.last_response = response
