"""When 點擊確認按鈕（確認移除 / 確認通用）— Command"""

from behave import when


@when('點擊「確認移除」按鈕')
def step_impl_confirm_remove(context):
    """確認移除操作，執行實際刪除。"""
    report_ref = context.memo.get("pending_delete_report")
    token = context.memo.get("admin_token")
    if report_ref and token:
        response = context.api_client.patch(
            f"/api/v1/admin/reports/{report_ref}/action",
            json={"action": "delete_and_warn", "note": "確認移除"},
            headers={"Authorization": f"Bearer {token}"},
        )
        context.last_response = response
    else:
        # No pending delete — fall through (Red phase 404 expected)
        context.last_response = context.last_response


@when('點擊「確認」按鈕')
def step_impl_confirm_generic(context):
    """確認通用操作（如重設速率限制、清除快取）。"""
    pending_action = context.memo.get("pending_system_action")
    token = context.memo.get("admin_token")
    if pending_action and token:
        response = context.api_client.post(
            f"/api/v1/admin/system/{pending_action}/confirm",
            headers={"Authorization": f"Bearer {token}"},
        )
        context.last_response = response


@when('於篩選選單切換為 "{status}"')
def step_impl_switch_filter(context, status):
    """切換篩選選單狀態並重新查詢。"""
    token = context.memo.get("admin_token")
    if token:
        response = context.api_client.get(
            f"/api/v1/admin/reports?status={status}",
            headers={"Authorization": f"Bearer {token}"},
        )
        context.last_response = response
        context.memo["report_filter_status"] = status
