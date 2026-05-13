"""Then API response checks — Feature 49 Chat Annotations BDD."""

from behave import then


@then('response status 為 {code:d}')
def step_response_status(context, code):
    actual = context.last_response.status_code
    assert actual == code, (
        f"預期 HTTP {code}，實際 {actual}：{context.last_response.text}"
    )


@then('response body 含 "{key1}", "{key2}", "{key3}", "{key4}"')
def step_response_body_contains_keys(context, key1, key2, key3, key4):
    data = context.last_response.json()
    for key in (key1, key2, key3, key4):
        assert key in data, f"response 缺少欄位 {key!r}，實際回應：{data}"


@then('response detail 含 "{text}"')
def step_response_detail_contains(context, text):
    data = context.last_response.json()
    detail = data.get("detail", "")
    assert text in detail, f"response detail 應含 '{text}'，實際：{detail!r}"


@then('response 的 total 為 {expected_total:d}')
def step_response_total(context, expected_total):
    # 可能是第一次 GET（list_response）或 filter GET（filtered_list_response）
    # 用最後一次 response
    data = context.last_response.json()
    actual = data.get("total")
    assert actual == expected_total, (
        f"expected total={expected_total}，actual total={actual}，回應：{data}"
    )
