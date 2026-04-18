"""Then 自訂科目相關斷言 — ReadModel Then (memo-based)"""

from behave import then


@then('已選科目列表應包含 "{subject}"')
def step_impl_selected_contains(context, subject):
    selected = context.memo.get("onboarding_selected_subjects", [])
    names = [s.get("subject_name") for s in selected]
    assert subject in names, f"已選科目列表應包含 '{subject}'，實際: {names}"


@then('該科目應標記為「自訂科目」')
def step_impl_marked_custom(context):
    name = context.memo.get("last_custom_subject")
    assert name, "memo 無 last_custom_subject"
    selected = context.memo.get("onboarding_selected_subjects", [])
    match = next((s for s in selected if s.get("subject_name") == name), None)
    assert match, f"找不到 '{name}' 於已選科目列表"
    assert match.get("is_custom") is True, f"is_custom 期望 True，實際 {match.get('is_custom')}"
