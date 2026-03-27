"""Then 頁面應顯示引導提示 — Readmodel Then"""

from behave import then


@then('頁面應顯示「請至少新增一個備考科目」引導提示')
def step_impl(context):
    data = context.last_response.json()
    assert data.get("guidance") == "請至少新增一個備考科目", \
        f"期望 guidance='請至少新增一個備考科目'，實際：{data}"


@then('頁面應顯示「+ 新增備考科目」入口')
def step_impl_add_subject(context):
    data = context.last_response.json()
    assert data.get("add_subject_entry") is True, \
        f"期望 add_subject_entry=True，實際：{data}"
