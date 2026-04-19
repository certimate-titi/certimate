"""Then 科目自評程度更新驗證 — ReadModel Then (memo-based)"""

from behave import then


@then('"{subject}" 的自評程度應更新為 "{expected_level}"')
def step_impl(context, subject, expected_level):
    selected = context.memo.get("onboarding_selected_subjects", [])
    match = next((s for s in selected if s.get("subject_name") == subject), None)
    assert match, f"找不到 '{subject}' 於已選科目列表"
    actual = match.get("self_assessed_level")
    assert actual == expected_level, \
        f"'{subject}' 的自評程度期望 '{expected_level}'，實際 '{actual}'"
