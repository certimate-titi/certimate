from behave import then


@then('預定使用的解析引擎應為 "{engine}"')
def step_impl(context, engine):
    response = context.last_response
    data = response.json()
    actual_engine = data.get("processing_engine") or data.get("resource", {}).get("processing_engine")
    assert actual_engine is not None, f"回應中找不到 processing_engine 欄位: {data}"
    assert actual_engine == engine, \
        f"解析引擎應為 '{engine}'，實際為 '{actual_engine}'"
