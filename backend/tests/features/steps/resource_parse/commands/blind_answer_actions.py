"""EPIC-035 M3 盲推論作答 When steps."""

from behave import when


def _auth(context, email):
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}'"
    return {"Authorization": f"Bearer {context.jwt_helper.generate_token(user_id)}"}


@when('使用者 "{email}" 對該題提交盲作答答案 "{answer}"')
def submit_blind_answer(context, email, answer):
    qid = context.memo["last_question_id"]
    context.last_response = context.api_client.post(
        f"/api/v1/questions/{qid}/blind-answer",
        headers=_auth(context, email),
        json={"answer": answer},
    )


@when('使用者 "{email}" 對該題提交推論判定 "{judgment}"')
def submit_inference_judgment(context, email, judgment):
    qid = context.memo["last_question_id"]
    context.last_response = context.api_client.post(
        f"/api/v1/questions/{qid}/inference-judgment",
        headers=_auth(context, email),
        json={"judgment": judgment},
    )
