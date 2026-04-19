"""Given 使用者已選擇科目並設定自評程度 — Aggregate Given"""

from behave import given


@given('使用者已選擇 "{subject}" 並設定自評程度為 "{level}"')
def step_impl(context, subject, level):
    """記錄使用者已選科目與自評程度到 memo。"""
    context.memo.setdefault("selected_subjects_with_level", {})[subject] = level
    selected = context.memo.setdefault("onboarding_selected_subjects", [])
    # 避免重覆加入
    for s in selected:
        if s.get("subject_name") == subject:
            s["self_assessed_level"] = level
            return
    selected.append({
        "subject_name": subject,
        "is_custom": False,
        "self_assessed_level": level,
    })


@given('使用者已選擇 "{subject}"')
def step_impl_selected_no_level(context, subject):
    """記錄使用者已選科目（未指定自評程度）到 memo。"""
    selected = context.memo.setdefault("onboarding_selected_subjects", [])
    for s in selected:
        if s.get("subject_name") == subject:
            return
    selected.append({
        "subject_name": subject,
        "is_custom": False,
        "self_assessed_level": "beginner",
    })
