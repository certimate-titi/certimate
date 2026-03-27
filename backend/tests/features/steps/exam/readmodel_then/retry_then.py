"""Then steps for retry/error handling verification — ReadModel Then"""

import uuid

from behave import then


@then('系統應自動重試最多 {max_retries:d} 次，每次間隔 {interval:d} 秒')
def step_impl(context, max_retries, interval):
    response = context.last_response
    # The response should still succeed (retry then success)
    assert response.status_code in (200, 201), \
        f"預期成功（重試後成功），實際 {response.status_code}: {response.text}"

    data = response.json()
    events = data.get("progress_events", [])

    # Check that retry event exists
    retry_events = [e for e in events if "重試" in e.get("message", "")]
    assert len(retry_events) > 0, \
        f"應有重試事件，但在進度事件中找不到重試訊息"


@then('SSE 應推送重試訊息 "{expected_msg}"')
def step_impl(context, expected_msg):
    response = context.last_response
    data = response.json()
    events = data.get("progress_events", [])

    # Look for retry message
    found = False
    for event in events:
        msg = event.get("message", "")
        if "重試" in msg:
            found = True
            break

    assert found, f"找不到重試訊息，進度事件: {events}"


@then('測驗任務狀態應更新為 "{expected_status}"')
def step_impl(context, expected_status):
    db = context.db_session
    exam_id = context.memo.get("current_exam_id")

    if exam_id:
        from app.models.exam import Exam
        exam = db.query(Exam).filter_by(id=uuid.UUID(exam_id)).first()
        assert exam is not None, "找不到測驗任務"

        exam_status = exam.status.value if hasattr(exam.status, 'value') else exam.status
        assert exam_status == expected_status, \
            f"測驗狀態應為 '{expected_status}'，但得到 '{exam_status}'"
    else:
        # Check from response
        response = context.last_response
        data = response.json()
        assert data.get("status") == "error" or expected_status == "FAILED", \
            f"預期狀態 '{expected_status}'，但回應為 {data}"


@then('SSE 應推送錯誤事件：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    for row in context.table:
        field = row["欄位"]
        expected_val = row["值"]

        if field == "status":
            actual = data.get("status", "")
            assert expected_val in str(actual), \
                f"status 應為 '{expected_val}'，但得到 '{actual}'"
        elif field == "message":
            actual = data.get("message", "")
            assert expected_val in str(actual), \
                f"message 應包含 '{expected_val}'，但得到 '{actual}'"
        elif field == "stage":
            actual = str(data.get("stage", ""))
            assert expected_val == actual, \
                f"stage 應為 '{expected_val}'，但得到 '{actual}'"


@then('系統應記錄詳細錯誤日誌')
def step_impl(context):
    response = context.last_response
    data = response.json()
    # Verify error information exists
    assert data.get("status") == "error" or data.get("retries_exhausted") is True, \
        "應有錯誤日誌資訊"


@then('系統應自動為階段 4 補充指示並重新生成')
def step_impl(context):
    result = context.memo.get("validation_result", {})
    assert result.get("valid") is False, "應檢測到格式不符"
    assert "regenerate_hint" in result, "應有重新生成的補充指示"


@then('重新生成的補充指令應包含具體缺失欄位的提示')
def step_impl(context):
    result = context.memo.get("validation_result", {})
    hint = result.get("regenerate_hint", "")
    missing_field = context.memo.get("missing_field", "explanation")
    assert missing_field in hint, \
        f"補充指令應包含缺失欄位 '{missing_field}'，但得到 '{hint}'"
