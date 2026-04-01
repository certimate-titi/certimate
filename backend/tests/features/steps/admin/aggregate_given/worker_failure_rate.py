"""Given 過去 N 小時 Worker 任務失敗率為 M% — Aggregate Given (mock)"""

from behave import given


@given('過去 {hours} 小時 Worker 任務失敗率為 {rate}%')
def step_impl(context, hours, rate):
    if not hasattr(context, "memo"):
        context.memo = {}
    context.memo["worker_failure_rate"] = int(rate)
    context.memo["worker_failure_hours"] = int(hours)
