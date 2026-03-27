"""Then 已選科目列表應僅顯示 — ReadModel Then"""

from behave import then


@then('已選科目列表應僅顯示 "{subject}"')
def step_impl(context, subject):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"
    data = response.json()

    # Check the removed subject is gone and expected subject remains
    selected = data.get("selected_subjects", [])
    names = [s.get("name") for s in selected]
    assert subject in names, \
        f"已選科目列表應包含 '{subject}'，實際: {names}"

    # The previously removed subject should not be in the list
    removed = context.memo.get("selected_subjects", [])
    for subj in removed:
        if subj != subject:
            assert subj not in names, \
                f"已移除的 '{subj}' 不應出現在列表中，實際: {names}"
