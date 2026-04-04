"""When AI 出題服務生成題目 — Command"""

from behave import when


@when('AI 出題服務生成 {count:d} 題選擇題')
def step_impl(context, count):
    user_id = context.memo.get("ai_gen_user_id")
    token = context.jwt_helper.generate_token(user_id) if user_id else None
    subject_id = context.memo.get("ai_gen_subject_id")

    response = context.api_client.post(
        "/api/v1/ai-questions/generate",
        headers={"Authorization": f"Bearer {token}"} if token else {},
        json={
            "subject_id": subject_id,
            "count": count,
        },
    )
    context.last_response = response


@when('匯入完成')
def step_import_done(context):
    subject_id = context.memo.get("import_subject_id")

    response = context.api_client.post(
        "/api/v1/questions/import",
        json={
            "subject_id": subject_id,
            "source_type": "historical",
        },
    )
    context.last_response = response
