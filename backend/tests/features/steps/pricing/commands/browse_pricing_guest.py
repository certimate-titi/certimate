"""When 訪客瀏覽定價比較頁 — Command"""

from behave import when


@when('訪客瀏覽定價比較頁')
def step_impl(context):
    response = context.api_client.get("/api/v1/pricing")
    context.last_response = response
