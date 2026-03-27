"""Then 回應應標示使用模型 — ReadModel Then"""

from behave import then


@then('回應應標示使用模型為 "{model}"')
def step_impl(context, model):
    response = context.last_response
    data = response.json()

    actual_model = data.get("model_used", data.get("model", ""))
    assert actual_model == model, (
        f"回應中的模型應為 '{model}'，但得到 '{actual_model}'"
    )
