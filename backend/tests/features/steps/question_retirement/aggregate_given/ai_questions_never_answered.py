"""Given 這些 AI 題從未被作答 — Aggregate Given"""

from behave import given


@given('這些 AI 題從未被作答')
def step_impl(context):
    # 預設就沒有 answers 記錄，確認 AI 題已建立即可
    assert "ai_question_ids" in context.memo, \
        "需先執行 Given 建立 AI 題目"
