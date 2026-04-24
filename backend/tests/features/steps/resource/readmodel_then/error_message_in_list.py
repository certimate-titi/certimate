"""Then 資源列表回應的 error_message 欄位驗證。"""

from behave import then


@then('該筆資源的 error_message 欄位應為「{expected}」')
def step_impl(context, expected):
    assert context.last_response.status_code == 200, (
        f"預期 200，實際 {context.last_response.status_code}: {context.last_response.text}"
    )
    body = context.last_response.json()
    resources = body.get("resources", [])
    resource_id = context.memo.get("last_resource_id")
    target = next((r for r in resources if r.get("id") == resource_id), None)
    assert target is not None, f"列表中找不到 id={resource_id} 的資源"
    assert target.get("error_message") == expected, (
        f"預期 error_message='{expected}'，實際={target.get('error_message')!r}"
    )
