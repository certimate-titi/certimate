"""EPIC-035 resource parse commands — When steps."""

from behave import when


def _auth(context, email):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}'"
    return {"Authorization": f"Bearer {context.jwt_helper.generate_token(user_id)}"}


@when('使用者 "{email}" 查詢該資源解析狀態')
def query_status(context, email):
    rid = context.memo["last_resource_id"]
    context.last_response = context.api_client.get(
        f"/api/v1/resources/{rid}/parse-status", headers=_auth(context, email)
    )


@when('使用者 "{email}" 查詢該資源候選題')
def query_candidates(context, email):
    rid = context.memo["last_resource_id"]
    context.last_response = context.api_client.get(
        f"/api/v1/resources/{rid}/question-candidates",
        headers=_auth(context, email),
    )


@when('使用者 "{email}" 批次核可該資源前 {n:d} 個 T2 候選題')
def approve_candidates(context, email, n):
    rid = context.memo["last_resource_id"]
    list_resp = context.api_client.get(
        f"/api/v1/resources/{rid}/question-candidates",
        headers=_auth(context, email),
    )
    assert list_resp.status_code == 200, list_resp.text
    t2_ids = [c["id"] for c in list_resp.json()["t2"][:n]]
    assert len(t2_ids) == n, f"T2 候選題不足：預期 {n}，實際 {len(t2_ids)}"

    context.last_response = context.api_client.post(
        f"/api/v1/resources/{rid}/question-candidates/approve",
        headers=_auth(context, email),
        json={"candidate_ids": t2_ids, "approve": True},
    )


@when('使用者 "{email}" 觸發該資源的 LLM 解析')
def trigger_parse(context, email):
    rid = context.memo["last_resource_id"]
    context.last_response = context.api_client.post(
        f"/api/v1/resources/{rid}/parse", headers=_auth(context, email)
    )
