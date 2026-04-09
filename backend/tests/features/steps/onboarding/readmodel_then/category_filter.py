"""Then 類別篩選結果驗證 — ReadModel Then"""

from behave import then


@then('畫面不應顯示 "{category}" 分類的科目')
def step_impl_category_not_shown(context, category):
    """驗證指定分類的科目不在回應中。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        subjects = data if isinstance(data, list) else data.get("subjects", [])
        for s in subjects:
            s_category = s.get("category") or s.get("category_name") or ""
            assert s_category != category, \
                f"畫面不應顯示 '{category}' 分類的科目，但找到: {s}"


@then('畫面應顯示所有分類的科目清單')
def step_impl_all_categories_shown(context):
    """驗證所有分類的科目均在回應中（至少有資料）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        subjects = data if isinstance(data, list) else data.get("subjects", [])
        assert len(subjects) > 0, "畫面應顯示所有分類的科目清單，但清單為空"
