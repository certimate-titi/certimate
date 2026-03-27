"""Then FREE 方案 basic 任務的主要模型應為 — Aggregate Then"""

from behave import then

from app.models.ai_model_routing import AiModelRouting


@then('{plan} 方案 {task_type} 任務的主要模型應為 "{expected_model}"')
def step_impl(context, plan, task_type, expected_model):
    db = context.db_session
    db.expire_all()
    routing = db.query(AiModelRouting).filter(
        AiModelRouting.plan == plan,
        AiModelRouting.task_type == task_type,
    ).first()
    assert routing is not None, f"找不到 {plan}/{task_type} 的模型路由設定"
    assert routing.primary_model == expected_model, \
        f"主要模型應為 '{expected_model}'，實際 '{routing.primary_model}'"
