from behave import then


@then('新建立的資源應標記 implicit_consent 為 true')
def step_impl(context):
    response = context.last_response
    data = response.json()
    implicit_consent = data.get("implicit_consent") or data.get("resource", {}).get("implicit_consent")
    assert implicit_consent is True, \
        f"implicit_consent 應為 True，實際為 {implicit_consent}: {data}"
