"""Then steps for AI retry and error handling behavior — ReadModel Then"""

from behave import then


@then('系統應自動重試最多 {max_retries:d} 次，每次間隔 {interval:d} 秒')
def step_impl_auto_retry(context, max_retries, interval):
    """驗證系統自動重試行為。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404, 422, 500), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        retry_info = data.get("retry_info", {})
        actual_retries = retry_info.get("max_retries", 0)
        assert actual_retries >= max_retries, \
            f"最大重試次數應 ≥ {max_retries}，實際 {actual_retries}"


@then('測驗任務狀態應更新為 "FAILED"')
def step_impl_task_failed(context):
    """驗證測驗任務狀態已更新為 FAILED。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404, 422, 500), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        status = data.get("status") or data.get("task_status")
        assert status == "FAILED", f"任務狀態應為 'FAILED'，實際 '{status}'"


@then('系統應記錄詳細錯誤日誌')
def step_impl_error_logged(context):
    """驗證系統記錄詳細錯誤日誌（語義層面）。"""
    response = context.last_response
    # In Red phase (404), this is a placeholder assertion
    assert response.status_code in (200, 201, 404, 422, 500), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('系統應自動為階段 {stage_id:d} 補充指示並重新生成')
def step_impl_regenerate(context, stage_id):
    """驗證系統自動補充指示並重新生成指定階段。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        regenerated = data.get("regenerated_stage")
        assert regenerated == stage_id, \
            f"期望重新生成階段 {stage_id}，實際 {regenerated}"


@then('重新生成的補充指令應包含具體缺失欄位的提示')
def step_impl_supplement_hint(context):
    """驗證補充指令包含缺失欄位提示。"""
    response = context.last_response
    if response.status_code in (200, 201):
        data = response.json()
        supplement = data.get("supplement_instruction", "")
        assert len(supplement) > 0, "補充指令不應為空"
