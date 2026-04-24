"""Given 測驗任務的 bloom_source / bloom_distribution — Aggregate Given."""

from behave import given


@given('測驗任務的 bloom_source 為 "historical"，bloom_distribution 為：')
def step_impl_historical_bloom(context):
    bloom_dist = {}
    for row in context.table:
        bloom_dist[row["bloom_category"]] = int(row["percentage"])
    context.memo["bloom_source"] = "historical"
    context.memo["bloom_distribution"] = bloom_dist


@given('測驗任務的 bloom_source 為 "default"')
def step_impl_default_bloom(context):
    context.memo["bloom_source"] = "default"
    context.memo["bloom_distribution"] = {
        "remember": 20,
        "understand": 25,
        "apply": 25,
        "analyze": 15,
        "evaluate": 10,
        "create": 5,
    }
