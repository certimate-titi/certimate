"""Then 科目切換器相關 — Readmodel Then"""

from behave import then


@then('科目切換器應包含：')
def step_impl(context):
    data = context.last_response.json()
    subjects = data.get("subjects", [])
    subject_names = [s["name"] for s in subjects]

    for row in context.table:
        expected = row["科目"]
        assert expected in subject_names, \
            f"科目切換器中找不到 '{expected}'，實際：{subject_names}"


@then('預設顯示 "{subject_name}" 的學習數據')
def step_impl_default(context, subject_name):
    data = context.last_response.json()
    active = data.get("active_subject")
    assert active == subject_name, \
        f"期望預設科目為 '{subject_name}'，實際：{active}"
