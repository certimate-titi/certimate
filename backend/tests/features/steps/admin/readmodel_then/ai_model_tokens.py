"""Then 回應應包含以下模型的 Token 消耗量 — Read Model Then"""

from behave import then


@then('回應應包含以下模型的 Token 消耗量：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    models_data = data.get("models", data.get("ai_cost", []))

    expected_models = [row["模型"] for row in context.table]

    actual_model_names = []
    if isinstance(models_data, list):
        actual_model_names = [m.get("model", m.get("name", "")) for m in models_data]
    elif isinstance(models_data, dict):
        actual_model_names = list(models_data.keys())

    for expected_model in expected_models:
        assert expected_model in actual_model_names, \
            f"回應缺少模型 '{expected_model}'，實際模型：{actual_model_names}"
