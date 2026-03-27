"""Then 系統應記錄審計日誌 — Aggregate Then"""

import uuid

from behave import then

from app.models.audit_log import AdminAuditLog


@then('系統應記錄審計日誌：')
def step_impl(context):
    db = context.db_session

    expected = {}
    for row in context.table:
        expected[row["欄位"]] = row["值"]

    logs = db.query(AdminAuditLog).all()
    assert len(logs) > 0, "沒有找到審計日誌"

    # Find matching log
    matched = None
    for log in logs:
        action = log.action
        if "action" in expected and action != expected["action"]:
            continue
        matched = log
        break

    assert matched is not None, \
        f"找不到符合條件的審計日誌，action={expected.get('action')}，實際 logs: {[(l.action, l.details) for l in logs]}"

    if "admin_id" in expected:
        expected_admin_key = expected["admin_id"]
        expected_admin_uuid = context.ids.get(expected_admin_key)
        if expected_admin_uuid:
            assert str(matched.admin_id) == expected_admin_uuid, \
                f"audit log admin_id 應為 '{expected_admin_uuid}'，實際 '{matched.admin_id}'"

    if "details" in expected:
        details_str = expected["details"]
        details = matched.details or {}
        # Check that the details contain the expected content
        details_full = str(details)
        assert details_str in details_full or any(
            details_str in str(v) for v in details.values()
        ), f"audit log details 應包含 '{details_str}'，實際 '{details}'"
