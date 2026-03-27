"""Then 導航列不應包含「系統設定」選項 — Read Model Then"""

from behave import then


@then('導航列不應包含「系統設定」選項')
def step_impl(context):
    response = context.last_response
    data = response.json()
    # admin role should have can_access_settings = False
    can_access = data.get("can_access_settings", False)
    assert can_access is False, \
        f"admin 不應有系統設定權限，但 can_access_settings={can_access}"
