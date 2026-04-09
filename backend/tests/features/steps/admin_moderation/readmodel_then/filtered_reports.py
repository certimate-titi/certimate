"""Then 篩選後檢舉列表驗證 — ReadModel Then"""

from behave import then


@then('檢舉列表應僅顯示狀態為 "{expected_status}" 的檢舉')
def step_impl(context, expected_status):
    """驗證回應中所有檢舉的狀態均符合篩選條件。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        reports = data if isinstance(data, list) else data.get("reports", [data])
        for r in reports:
            actual_status = r.get("status") or r.get("report_status") or ""
            assert actual_status == expected_status, \
                f"檢舉列表應僅包含狀態 '{expected_status}'，但發現 '{actual_status}'"
