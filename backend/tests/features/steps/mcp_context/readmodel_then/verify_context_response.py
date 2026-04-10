"""
驗證 MCP Context Server 的回應
"""

from behave import then


@then('回應狀態為 "{status}"')
def step_verify_response_status(context, status):
    """驗證回應的狀態"""
    response = context.last_response

    if status == "success":
        assert response.get("error") == False, f"Expected success but got error: {response.get('message')}"
    elif status == "error":
        assert response.get("error") == True, f"Expected error but got success"
    else:
        raise ValueError(f"Unknown status: {status}")


@then('回應包含弱點領域 "{topic}"')
def step_verify_weak_area_in_response(context, topic):
    """驗證回應包含指定的弱點領域"""
    response = context.last_response
    data = response.get("data", {})
    weak_areas = data.get("weak_areas", [])

    topics = [wa.get("topic") for wa in weak_areas]
    assert topic in topics, f"Expected topic {topic} in weak areas: {topics}"


@then('回應包含 "{email}" 的顯示名稱')
def step_verify_display_name(context, email):
    """驗證回應包含用戶的顯示名稱"""
    response = context.last_response
    data = response.get("data", {})
    display_name = data.get("display_name")

    assert display_name is not None, "No display name in response"


@then('回應包含 {count:d} 筆錯誤記錄')
def step_verify_error_count(context, count):
    """驗證回應包含指定數量的錯誤記錄"""
    response = context.last_response
    data = response.get("data", {})
    errors = data.get("errors", [])

    assert len(errors) == count, f"Expected {count} errors but got {len(errors)}"


@then('回應包含錯誤模式分析')
def step_verify_error_patterns(context):
    """驗證回應包含錯誤模式分析"""
    response = context.last_response
    data = response.get("data", {})
    patterns = data.get("error_patterns", [])

    assert isinstance(patterns, list), "error_patterns should be a list"


@then('回應包含視覺學習偏好分數')
def step_verify_visual_preference(context):
    """驗證回應包含視覺學習偏好分數"""
    response = context.last_response
    data = response.get("data", {})
    visual_pref = data.get("visual_preference")

    assert visual_pref is not None, "No visual_preference in response"
    assert 0.0 <= visual_pref <= 1.0, f"visual_preference should be 0.0-1.0, got {visual_pref}"


@then('回應包含最優間隔複習天數')
def step_verify_spacing_interval(context):
    """驗證回應包含最優間隔複習天數"""
    response = context.last_response
    data = response.get("data", {})
    interval = data.get("optimal_spacing_interval")

    assert interval is not None, "No optimal_spacing_interval in response"
    assert isinstance(interval, int), f"optimal_spacing_interval should be int, got {type(interval)}"


@then('每筆記錄包含題目 ID、知識點、答題時間')
def step_verify_error_record_fields(context):
    """驗證每筆錯誤記錄包含必要字段"""
    response = context.last_response
    data = response.get("data", {})
    errors = data.get("errors", [])

    required_fields = ["question_id", "topic", "error_at"]
    for error in errors:
        for field in required_fields:
            assert field in error, f"Missing field {field} in error record: {error}"


@then('回應包含錯誤訊息 "{expected_message}"')
def step_verify_error_message(context, expected_message):
    """驗證回應包含指定的錯誤訊息"""
    response = context.last_response
    message = response.get("message", "")

    assert expected_message in message, f"Expected '{expected_message}' in message, got: {message}"
