"""Then 不應建立 Resource 紀錄。"""

import uuid
from behave import then

from app.models.resource import Resource


@then('不應建立 Resource 紀錄')
def step_impl(context):
    db = context.db_session
    user_id_str = context.memo.get("uploader_user_id")
    assert user_id_str, "找不到 uploader_user_id，請先執行上傳 step"
    count = db.query(Resource).filter(Resource.user_id == uuid.UUID(user_id_str)).count()
    assert count == 0, f"預期無 Resource，實際有 {count} 筆"
