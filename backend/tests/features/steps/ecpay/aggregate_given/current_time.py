"""Given 目前時間為 — Aggregate Given"""

from datetime import datetime, timezone

from behave import given

from app.services.ecpay_service import set_now_func


@given('目前時間為 "{time_str}"')
def step_impl(context, time_str):
    context.memo["current_time"] = time_str
    # 解析時間並注入到 ecpay_service
    fixed_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    set_now_func(lambda: fixed_time)
