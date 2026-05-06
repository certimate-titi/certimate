"""Then 驗證 delete-preview / hard-delete API 的回應結構。"""

from behave import then


def _json(context):
    return context.last_response.json()


@then('系統應回傳 {code:d}')
def step_status_code(context, code):
    actual = context.last_response.status_code
    assert actual == code, f"預期 {code}，實際 {actual}: {context.last_response.text}"


@then('系統應回傳 {a:d} 或 {b:d}')
def step_status_code_either(context, a, b):
    actual = context.last_response.status_code
    assert actual in (a, b), (
        f"預期 {a} 或 {b}，實際 {actual}: {context.last_response.text}"
    )


@then('回應的 subject_name 應為 "{name}"')
def step_resp_subject_name(context, name):
    body = _json(context)
    assert body.get("subject_name") == name, (
        f"預期 subject_name={name}，實際 {body.get('subject_name')}"
    )


@then('回應的 resource_name 應為 "{name}"')
def step_resp_resource_name(context, name):
    body = _json(context)
    assert body.get("resource_name") == name, (
        f"預期 resource_name={name}，實際 {body.get('resource_name')}"
    )


@then('回應 cascade_count 應包含欄位 "{f1}"、"{f2}"、"{f3}"')
def step_cascade_has_fields(context, f1, f2, f3):
    body = _json(context)
    cc = body.get("cascade_count", {})
    for f in (f1, f2, f3):
        assert f in cc, f"cascade_count 缺欄位 {f}（實際: {list(cc.keys())}）"


@then('回應 cascade_count.{field} 應為 {expected:d}')
def step_cascade_field_value(context, field, expected):
    body = _json(context)
    cc = body.get("cascade_count", {})
    actual = cc.get(field)
    assert actual == expected, (
        f"預期 cascade_count.{field}={expected}，實際 {actual}"
    )
