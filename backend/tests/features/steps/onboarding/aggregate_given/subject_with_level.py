"""Given 使用者已選擇科目並設定自評程度 — Aggregate Given"""

from behave import given


@given('使用者已選擇 "{subject}" 並設定自評程度為 "{level}"')
def step_impl(context, subject, level):
    """記錄使用者已選科目與自評程度到 memo。"""
    context.memo.setdefault("selected_subjects_with_level", {})[subject] = level
