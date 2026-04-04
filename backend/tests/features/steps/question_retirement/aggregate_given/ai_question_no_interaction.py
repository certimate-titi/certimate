"""Given 該題未加入錯題本、未被收藏、未標記為危險盲點 — Aggregate Given"""

from behave import given


@given('該題未加入錯題本、未被收藏、未標記為危險盲點')
def step_impl(context):
    # 預設就沒有這些記錄，不需額外操作
    assert "current_question_id" in context.memo, \
        "需先執行 Given 建立 AI 題目"
