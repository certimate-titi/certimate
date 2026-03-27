"""Then 回應應包含有效的測驗 ID — ReadModel Then"""

from behave import then


@then('回應應包含有效的測驗 ID')
def step_impl(context):
    response = context.last_response
    data = response.json()

    exam_id = data.get("exam_id")
    assert exam_id, "回應應包含 exam_id 欄位"
    assert len(str(exam_id)) > 0, "exam_id 不應為空"
