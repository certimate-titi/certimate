from behave import then


@then('登入成功不會報錯')
def step_impl(context):
    response = context.last_response
    assert response.status_code in [200, 201], \
        f"登入應成功（2XX），實際 {response.status_code}: {response.text}"

    data = response.json()
    error = data.get("error") or data.get("detail")
    assert error is None, \
        f"登入回應不應包含錯誤訊息，但發現: {error}"
