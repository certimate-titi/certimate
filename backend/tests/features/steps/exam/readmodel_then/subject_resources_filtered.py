"""Then 列表中應僅顯示指定學科且狀態為 COMPLETED 的資源 — ReadModel Then"""

from behave import then


@then('"{label}" 列表中應僅顯示 subjectId 為 "{subject_id}" 且狀態為 COMPLETED 的資源')
def step_impl(context, label, subject_id):
    response = context.last_response
    data = response.json()

    resources = data.get("resources", [])
    for r in resources:
        assert r.get("subject_id") == subject_id, (
            f"資源 subject_id 應為 '{subject_id}'，但得到 '{r.get('subject_id')}'"
        )
        assert r.get("status") == "COMPLETED", (
            f"資源狀態應為 'COMPLETED'，但得到 '{r.get('status')}'"
        )
