"""Then 回應中每筆紀錄應包含審計日誌欄位 — Readmodel Then"""

from behave import then

REQUIRED_FIELDS = [
    "timestamp",
    "admin_id",
    "action",
    "target_type",
    "target_id",
    "details",
    "ip_address",
]


@then('回應中每筆紀錄應包含審計日誌欄位')
def step_impl(context):
    response = context.last_response
    data = response.json()

    # Response could be {"logs": [...]} or a list directly
    logs = data if isinstance(data, list) else data.get("logs", data.get("items", []))

    # If empty logs, still verify structure by checking the endpoint returned something usable
    # When there are 0 logs, we just verify the response shape is valid (list)
    assert isinstance(logs, list), f"期望回傳列表，實際 {type(logs)}: {data}"
    # If logs exist, check fields
    for record in logs:
        for field in REQUIRED_FIELDS:
            assert field in record, \
                f"紀錄缺少欄位 '{field}'，實際 keys: {list(record.keys())}"
