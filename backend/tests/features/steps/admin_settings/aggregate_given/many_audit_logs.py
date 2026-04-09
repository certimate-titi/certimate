"""Given 系統中有超過 N 筆稽核日誌紀錄 — Aggregate Given"""

from behave import given


@given('系統中有超過 {count:d} 筆稽核日誌紀錄')
def step_impl(context, count):
    """記錄稽核日誌數量到 memo（Red 階段僅設置狀態）。"""
    context.memo["many_audit_logs_count"] = count
