"""Then 分類下應包含科目 — ReadModel Then"""

from behave import then


@then('"{category}" 分類下應包含 "{subject_name}"')
def step_impl(context, category, subject_name):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"

    data = response.json()
    categories = data.get("categories", [])

    target_cat = None
    for cat in categories:
        if cat.get("category") == category:
            target_cat = cat
            break

    assert target_cat is not None, \
        f"找不到分類 '{category}'，實際分類: {[c['category'] for c in categories]}"

    subject_names = [s["name"] for s in target_cat.get("subjects", [])]
    assert subject_name in subject_names, \
        f"分類 '{category}' 下應包含 '{subject_name}'，實際: {subject_names}"
