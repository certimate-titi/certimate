"""Then 待確認放榜清單驗證 — ReadModel"""

from behave import then


@then('待確認清單應包含科目 "{subject_name}"')
def step_pending_contains(context, subject_name):
    items = context.last_response.json().get("items", [])
    names = [it.get("subject_name") for it in items]
    assert subject_name in names, f"清單未包含 {subject_name}；實際: {names}"


@then('待確認清單不應包含科目 "{subject_name}"')
def step_pending_not_contains(context, subject_name):
    items = context.last_response.json().get("items", [])
    names = [it.get("subject_name") for it in items]
    assert subject_name not in names, f"清單不應包含 {subject_name}；實際: {names}"
