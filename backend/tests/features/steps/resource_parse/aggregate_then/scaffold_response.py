"""EPIC-035 M7 scaffold Then — DB 驗證。"""

import uuid

from behave import then

from app.models.resource_scaffold import ResourceScaffold


@then('DB 中該鷹架的 user_response 應包含 "{text}"')
def step_impl(context, text):
    sid = uuid.UUID(context.memo["last_submitted_scaffold_id"])
    s = context.db_session.get(ResourceScaffold, sid)
    assert s is not None, f"找不到鷹架 {sid}"
    response = s.user_response or ""
    assert text in response, \
        f"user_response 未包含 '{text}'，實際：{response!r}"
