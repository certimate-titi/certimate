"""When 後端 AI 生成服務開始處理 — Command"""

import uuid

from behave import when


@when('後端 AI 生成服務開始處理')
def step_impl(context):
    exam_id = context.memo.get("current_exam_id")
    email = context.memo.get("current_user_email")

    if not exam_id:
        # Need to create exam first - find user and create
        email = email or next(
            (k for k in context.ids if "@" in k), None
        )
        if not email:
            raise KeyError("找不到使用者 email")

        user_id = context.ids[email]
        subject_id = context.ids.get("default_subject", str(uuid.uuid4()))

        # Create exam via API
        token = context.jwt_helper.generate_token(user_id)

        # Get node IDs
        node_ids = []
        for key, val in context.ids.items():
            if key.startswith("node_"):
                node_ids.append(val)

        response = context.api_client.post(
            "/api/v1/exams/config",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "node_ids": node_ids[:2],
                "question_count": 10,
                "difficulty_distribution": {"easy": 30, "medium": 50, "hard": 20},
            },
        )
        if response.status_code in (200, 201):
            data = response.json()
            exam_id = data.get("exam_id")
            context.memo["current_exam_id"] = exam_id
        else:
            context.last_response = response
            return

    if not email:
        email = next((k for k in context.ids if "@" in k), None)
    user_id = context.ids.get(email)
    if not user_id:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    token = context.jwt_helper.generate_token(user_id)
    response = context.api_client.post(
        f"/api/v1/exams/{exam_id}/generate",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
