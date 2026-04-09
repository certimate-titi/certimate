"""Given 測驗任務的 bloom_source 與 bloom_distribution 設定 — Aggregate Given"""

from behave import given


@given('測驗任務的 bloom_source 為 "historical"，bloom_distribution 為：')
def step_impl_historical_bloom(context):
    """設定使用歷史考古題 Bloom 分佈的測驗任務。"""
    bloom_dist = {}
    for row in context.table:
        bloom_dist[row["bloom_category"]] = int(row["percentage"])
    context.memo["bloom_source"] = "historical"
    context.memo["bloom_distribution"] = bloom_dist


@given('測驗任務的 bloom_source 為 "default"')
def step_impl_default_bloom(context):
    """設定使用預設 Bloom 分佈的測驗任務。"""
    context.memo["bloom_source"] = "default"
    context.memo["bloom_distribution"] = {
        "remember": 20,
        "understand": 25,
        "apply": 25,
        "analyze": 15,
        "evaluate": 10,
        "create": 5,
    }


@given('使用者 "{email}" 已提交測驗設定並建立測驗任務 ID 為 {task_id:d}')
def step_impl_exam_task(context, email, task_id):
    """設定已提交測驗設定的使用者及任務 ID。"""
    context.memo["current_user_email"] = email
    context.memo["exam_task_id"] = task_id
