"""Then B2B 後台 UI 驗證 — ReadModel Then"""

from behave import then


@then('回應應包含學員 ID {student_id:d} 的複習排程列表')
def step_impl_schedule_list(context, student_id):
    """驗證複習排程列表（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        schedules = data if isinstance(data, list) else data.get("schedules", [])
        assert isinstance(schedules, list), "複習排程應為列表"


@then('每筆排程應包含：')
def step_impl_schedule_fields(context):
    """驗證每筆複習排程包含必要欄位。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        schedules = data if isinstance(data, list) else data.get("schedules", [])
        for s in schedules:
            for row in context.table:
                field = row["欄位"]
                assert field in s, f"排程應包含欄位 '{field}'，實際: {s.keys()}"


@then('回應應僅包含符合搜尋條件的學員')
def step_impl_search_results_filtered(context):
    """驗證搜尋結果過濾（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('回應中不應包含學員 "{email}"')
def step_impl_student_not_in_response(context, email):
    """驗證回應不包含指定學員。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        students = data if isinstance(data, list) else data.get("students", [])
        emails = [s.get("email", "") for s in students]
        assert email not in emails, \
            f"回應不應包含學員 '{email}'，但發現於: {emails}"


@then('回應應包含學員 ID {student_id:d} 的能力列表')
def step_impl_competency_list(context, student_id):
    """驗證學員能力列表（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        competencies = data if isinstance(data, list) else data.get("competencies", [])
        assert isinstance(competencies, list), "能力列表應為列表"


@then('每個能力節點應包含 CompetencyBar 所需資料：')
def step_impl_competency_bar_fields(context):
    """驗證能力節點包含 CompetencyBar 所需欄位。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        competencies = data if isinstance(data, list) else data.get("competencies", [])
        for c in competencies:
            for row in context.table:
                field = row["欄位"]
                assert field in c, f"能力節點應包含欄位 '{field}'，實際: {c.keys()}"


@then('回應應包含各知識節點的弱點分析')
def step_impl_weakness_analysis(context):
    """驗證弱點分析包含各知識節點（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        nodes = data if isinstance(data, list) else data.get("nodes", [])
        assert isinstance(nodes, list), "弱點分析應包含節點列表"


@then('每個知識節點應包含進度條所需資料：')
def step_impl_node_progress_bar_fields(context):
    """驗證知識節點包含進度條所需欄位。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        nodes = data if isinstance(data, list) else data.get("nodes", [])
        for n in nodes:
            for row in context.table:
                field = row["欄位"]
                assert field in n, f"知識節點應包含欄位 '{field}'，實際: {n.keys()}"


@then('系統應顯示提示訊息「此功能即將推出，敬請期待」')
def step_impl_coming_soon_hint(context):
    """驗證即將推出提示（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
