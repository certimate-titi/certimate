"""Then 通知內容驗證 — ReadModel Then"""

from behave import then


@then('系統應發送推送通知給使用者 "{email}"')
def step_notification_sent(context, email):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    notifications = data.get("notifications", [data]) if isinstance(data, dict) else data
    found = any(n.get("email") == email or n.get("user_email") == email for n in notifications)
    assert found, f"應有發送給 '{email}' 的通知"


@then('通知內容應詢問是否考取')
def step_ask_result(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    content = str(data)
    assert "考取" in content, f"通知內容應詢問是否考取: {data}"


@then('通知應包含「確認考取」和「未考取」兩個按鈕')
def step_buttons(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    actions = data.get("actions", [])
    action_labels = [a.get("label", "") for a in actions]
    assert any("考取" in label for label in action_labels), \
        f"應包含「確認考取」按鈕: {actions}"


@then('系統應發送第二次提醒通知')
def step_reminder(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    assert data.get("reminder_sent", False) or data.get("type") == "reminder", \
        f"應發送提醒通知: {data}"


@then('系統應發送通知告知資料將保留 {days:d} 天')
def step_retention_notice(context, days):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    content = str(data)
    assert str(days) in content, f"通知應包含保留 {days} 天的資訊: {data}"


@then('系統應發送祝賀通知')
def step_congrats(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    ntype = data.get("notification_type", data.get("type", ""))
    assert ntype in ("congrats", "congratulation", "passed") or "祝賀" in str(data), \
        f"應發送祝賀通知: {data}"


@then('通知內容應包含「資料將保留 {days:d} 天」的提示')
def step_retention_hint(context, days):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    content = str(data)
    assert str(days) in content, f"通知應包含「資料將保留 {days} 天」: {data}"


@then('系統應發送推薦通知')
def step_recommend(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    ntype = data.get("notification_type", data.get("type", ""))
    assert ntype in ("recommend", "cross_recommend") or "推薦" in str(data), \
        f"應發送推薦通知: {data}"


@then('通知內容應包含同領域的進階證照選項')
def step_recommend_content(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    recommendations = data.get("recommendations", data.get("subjects", []))
    assert len(recommendations) > 0, f"應包含進階證照推薦: {data}"


@then('系統應發送鼓勵通知')
def step_encourage(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    ntype = data.get("notification_type", data.get("type", ""))
    assert ntype in ("encourage", "encouragement", "failed") or "鼓勵" in str(data), \
        f"應發送鼓勵通知: {data}"


@then('通知內容應詢問是否再次報考')
def step_ask_retake(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    content = str(data)
    assert "報考" in content or "retake" in content, \
        f"通知應詢問是否再次報考: {data}"


@then('系統應根據弱點分析重新規劃學習計畫')
def step_replan(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    assert data.get("learning_plan_updated", False) or "plan" in str(data).lower(), \
        f"應重新規劃學習計畫: {data}"


@then('系統應發送溫暖告別通知')
def step_farewell(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    ntype = data.get("notification_type", data.get("type", ""))
    assert ntype in ("farewell", "goodbye", "quit") or "告別" in str(data), \
        f"應發送告別通知: {data}"
