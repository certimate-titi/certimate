"""EPIC-035 M7 scaffold commands — When steps."""

from behave import when


def _auth(context, email):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}'"
    return {"Authorization": f"Bearer {context.jwt_helper.generate_token(user_id)}"}


@when('使用者 "{email}" 取得該資源的 parsed 內容')
def get_parsed(context, email):
    rid = context.memo["last_resource_id"]
    context.last_response = context.api_client.get(
        f"/api/v1/resources/{rid}/parsed", headers=_auth(context, email)
    )


@when('使用者 "{email}" 對該資源第 {idx:d} 筆鷹架提交作答內容 "{content}"')
def submit_scaffold_response(context, email, idx, content):
    sid = context.memo["last_scaffold_ids"][idx - 1]
    context.memo["last_submitted_scaffold_id"] = sid
    context.last_response = context.api_client.post(
        f"/api/v1/resource-scaffolds/{sid}/response",
        headers=_auth(context, email),
        json={"content": content},
    )
