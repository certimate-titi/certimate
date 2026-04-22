"""EPIC-035 M4 練習提交作答 When step。"""

from behave import when


def _auth(context, email):
    user_id = context.ids.get(email)
    return {"Authorization": f"Bearer {context.jwt_helper.generate_token(user_id)}"}


@when('使用者 "{email}" 在練習模式提交該題答案 "{answer}"')
def submit_practice(context, email, answer):
    qid = context.memo["last_question_id"]
    context.last_response = context.api_client.post(
        "/api/v1/practice/submit",
        headers=_auth(context, email),
        json={"question_id": qid, "selected_answer": answer},
    )
