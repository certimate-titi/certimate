"""EPIC-035 readmodel Then steps — 回應欄位驗證."""

from behave import then


def _json(context):
    assert context.last_response is not None, "無 last_response"
    return context.last_response.json()


@then('回應欄位 "{field}" 應為 true')
def field_true(context, field):
    data = _json(context)
    assert data.get(field) is True, \
        f"欄位 '{field}' 應為 true，實際：{data.get(field)!r}"


@then('回應欄位 "{field}" 應為 false')
def field_false(context, field):
    data = _json(context)
    assert data.get(field) is False, \
        f"欄位 '{field}' 應為 false，實際：{data.get(field)!r}"


@then('回應欄位 "{field}" 應為 null')
def field_null(context, field):
    data = _json(context)
    assert data.get(field) is None, \
        f"欄位 '{field}' 應為 null，實際：{data.get(field)!r}"


@then('回應欄位 "{field}" 應為 {value:d}')
def field_equals_int(context, field, value):
    data = _json(context)
    actual = data.get(field)
    assert actual == value, f"欄位 '{field}' 期望 {value}，實際 {actual}"


@then('回應的 "{field}" 陣列應有 {n:d} 個項目')
def array_len(context, field, n):
    data = _json(context)
    arr = data.get(field)
    assert isinstance(arr, list), f"欄位 '{field}' 不是陣列：{type(arr)}"
    assert len(arr) == n, f"'{field}' 期望 {n} 項，實際 {len(arr)}"


@then('回應應包含升級引導欄位 "{field}"')
def upgrade_hint(context, field):
    data = _json(context)
    detail = data.get("detail", data)
    assert isinstance(detail, dict) and field in detail, \
        f"回應缺少 '{field}' 欄位：{data}"
