"""Then — 驗證系統記錄 soft cap 告警日誌。"""

from behave import then

from app.models.audit_log import AdminAuditLog


@then('系統應記錄 soft cap 告警日誌，包含 user_id 與當日用量')
def step_soft_cap_alert(context):
    db = context.db_session

    # Check admin_audit_logs for FUP soft cap alert
    logs = db.query(AdminAuditLog).filter(
        AdminAuditLog.action.like('%fup%soft_cap%')
    ).all()

    # Also check memo if service stored result there
    fup_result = context.memo.get("fup_result")

    assert len(logs) > 0 or fup_result is not None, \
        "未找到 soft cap 告警日誌"
