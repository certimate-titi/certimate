"""Then elaborative 鷹架 reference_answer 非空（TASK-03）— Aggregate Then"""

from behave import then

from app.models.resource import Resource
from app.models.resource_scaffold import ResourceScaffold, ResourceScaffoldType


@then('該資源的 elaborative 鷹架 reference_answer 欄位應非空')
def step_impl(context):
    db = context.db_session

    resource = (
        db.query(Resource)
        .filter(Resource.name == "延伸題測試.pdf")
        .order_by(Resource.created_at.desc())
        .first()
    )
    assert resource is not None, "找不到測試資源"

    rows = (
        db.query(ResourceScaffold)
        .filter(
            ResourceScaffold.resource_id == resource.id,
            ResourceScaffold.type == ResourceScaffoldType.ELABORATIVE.value,
        )
        .all()
    )
    assert rows, "elaborative 鷹架筆數為 0"
    for r in rows:
        assert r.reference_answer and r.reference_answer.strip(), (
            f"scaffold {r.id} reference_answer 為空"
        )
