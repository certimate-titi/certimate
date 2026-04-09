"""Given 錯題複習頁面狀態設置 — Aggregate Given"""

from behave import given


@given('使用者 "{email}" 已進入測驗 {exam_id:d} 的錯題複習頁面')
def step_impl_entered_review(context, email, exam_id):
    """記錄使用者已進入指定測驗的錯題複習頁面。"""
    context.memo["review_exam_id"] = exam_id
    context.memo["review_email"] = email


@given('側邊列表顯示題目 {q1:d} 與題目 {q2:d}')
def step_impl_sidebar_questions(context, q1, q2):
    """記錄側邊列表顯示的題目。"""
    context.memo["sidebar_questions"] = [q1, q2]


@given('使用者 "{email}" 查看測驗 {exam_id:d} 的錯題解析')
def step_impl_viewing_wrong_analysis(context, email, exam_id):
    """記錄使用者正在查看錯題解析的狀態。"""
    context.memo["wrong_analysis_email"] = email
    context.memo["wrong_analysis_exam_id"] = exam_id


@given('使用者 "{email}" 本月基礎教練已使用 {count:d} 次')
def step_impl_coach_quota_used(context, email, count):
    """記錄使用者本月基礎教練使用次數（已用完）。"""
    context.memo["coach_quota_used"] = count
    context.memo["coach_quota_email"] = email


@given('使用者 "{email}" 的所有測驗均無錯題記錄')
def step_impl_no_wrong_records(context, email):
    """記錄使用者無任何錯題記錄的狀態。"""
    context.memo["no_wrong_records_email"] = email
