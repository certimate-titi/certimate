"""Then 退場掃描統計與告警驗證 — ReadModel Then"""

from behave import then


@then('掃描應記錄以下統計：')
def step_impl(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()

    # 驗證 DataTable 中列出的統計欄位存在
    for row in context.table:
        metric = row["指標"]
        if metric == "軟刪除題數":
            assert "soft_deleted_count" in data or "soft_deleted" in str(data), \
                f"應包含軟刪除題數統計: {data}"
        elif metric == "硬刪除題數":
            assert "hard_deleted_count" in data or "hard_deleted" in str(data), \
                f"應包含硬刪除題數統計: {data}"
        elif metric == "保護跳過題數":
            assert "skipped_count" in data or "protected" in str(data), \
                f"應包含保護跳過題數統計: {data}"


@then('掃描日誌應保留供審計')
def step_audit_log(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    assert data.get("audit_logged", False) or data.get("log_id"), \
        f"掃描日誌應保留供審計: {data}"


@then('系統應暫停退場並觸發告警通知管理員')
def step_alert(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    assert data.get("alert_triggered", False) or data.get("paused", False), \
        f"應暫停退場並觸發告警: {data}"


@then('告警內容應包含「異常大量退場：{count} 題」')
def step_alert_content(context, count):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    alert_msg = data.get("alert_message", str(data))
    assert count in alert_msg, \
        f"告警應包含 '{count}': {alert_msg}"
