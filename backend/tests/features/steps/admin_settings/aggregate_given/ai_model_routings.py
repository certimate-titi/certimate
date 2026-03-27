"""Given 系統中有以下 AI 模型路由設定 — Aggregate Given"""

from behave import given

from app.models.ai_model_routing import AiModelRouting


@given('系統中有以下 AI 模型路由設定：')
def step_impl(context):
    db = context.db_session

    for row in context.table:
        routing = AiModelRouting(
            plan=row["方案"],
            task_type=row["任務類型"],
            primary_model=row["主要模型"],
            fallback_model=row.get("備援模型") or None,
        )
        db.add(routing)

    db.commit()
