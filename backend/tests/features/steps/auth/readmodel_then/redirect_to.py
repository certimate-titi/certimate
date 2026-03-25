from behave import then


PAGE_MAP = {
    "首次登入引導頁": "/onboarding",
    "個人儀表板首頁": "/dashboard",
}


@then('系統應導向至 "{page}"')
def step_impl(context, page):
    response = context.last_response
    data = response.json()
    redirect_to = data.get("redirect_to") or data.get("redirect")
    expected_path = PAGE_MAP.get(page, page)

    assert redirect_to is not None, \
        f"回應中找不到 redirect 欄位: {data}"
    assert redirect_to == expected_path, \
        f"應導向至 '{expected_path}'，實際為 '{redirect_to}'"
