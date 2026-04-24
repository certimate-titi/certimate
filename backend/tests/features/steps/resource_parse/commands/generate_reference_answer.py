"""When 系統為 elaborative 鷹架預產 AI 參考答案（TASK-03）— Command（stub）"""

from behave import when

from app.models.resource import Resource
from app.models.resource_scaffold import ResourceScaffold, ResourceScaffoldType
from app.services import resource_parse_service


@when('系統為該資源的 elaborative 鷹架預產 AI 參考答案（stub）')
def step_impl(context):
    db = context.db_session

    resource = (
        db.query(Resource)
        .filter(Resource.name == "延伸題測試.pdf")
        .order_by(Resource.created_at.desc())
        .first()
    )
    if resource is None:
        raise AssertionError("找不到測試資源 '延伸題測試.pdf'")

    rows = (
        db.query(ResourceScaffold)
        .filter(
            ResourceScaffold.resource_id == resource.id,
            ResourceScaffold.type == ResourceScaffoldType.ELABORATIVE.value,
        )
        .all()
    )

    original = resource_parse_service._call_gemini_reference_answer
    resource_parse_service._call_gemini_reference_answer = (
        lambda question, heading: "這是 stub 的參考答案：涵蓋 A、B 兩點與考點提示。"
    )
    try:
        resource_parse_service._generate_reference_answers(rows)
    finally:
        resource_parse_service._call_gemini_reference_answer = original

    db.flush()
    db.commit()
