"""Given 使用者的上次測驗得分與本次得分 — Aggregate Given"""

from behave import given


@given('使用者 "{email}" 的上次測驗得分為 {prev_score:d}，本次測驗 {exam_id:d} 得分為 {curr_score:d}')
def step_impl_score_history(context, email, prev_score, exam_id, curr_score):
    """記錄分數歷史到 memo（Red 階段僅設置狀態）。"""
    context.memo["score_history"] = {
        "email": email,
        "prev_score": prev_score,
        "exam_id": exam_id,
        "curr_score": curr_score,
    }


@given('使用者 "{email}" 查看測驗 {exam_id:d} 的結果')
def step_impl_viewing_result(context, email, exam_id):
    """記錄正在查看測驗結果的使用者狀態。"""
    context.memo["viewing_exam_result"] = {"email": email, "exam_id": exam_id}


@given('測驗 {exam_id:d} 的知識點分析中存在答對率低於 {threshold:d}% 的節點')
def step_impl_low_accuracy_node(context, exam_id, threshold):
    """記錄有低答對率節點的狀態。"""
    context.memo["low_accuracy_exam_id"] = exam_id
    context.memo["low_accuracy_threshold"] = threshold
