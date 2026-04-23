"""Analytics BDD — POST /analytics/events."""

import json
import uuid

from behave import when


@when('使用者 "{email}" 送出 Analytics 事件批次：')
def step_send_events(context, email):
    user_id = uuid.UUID(context.ids[email])
    token = context.jwt_helper.generate_token(user_id)

    events = []
    for row in context.table:
        props = json.loads(row["props"]) if row["props"].strip() else None
        events.append({
            "name": row["name"],
            "ts": int(row["ts"]),
            "props": props,
        })

    context.last_response = context.api_client.post(
        "/api/v1/analytics/events",
        json={"events": events},
        headers={"Authorization": f"Bearer {token}"},
    )


@when('使用者 "{email}" 送出空 Analytics 批次')
def step_send_empty(context, email):
    user_id = uuid.UUID(context.ids[email])
    token = context.jwt_helper.generate_token(user_id)
    context.last_response = context.api_client.post(
        "/api/v1/analytics/events",
        json={"events": []},
        headers={"Authorization": f"Bearer {token}"},
    )
