"""Then 題目已選答案應為 — ReadModel Then"""

from behave import then


@then('題目 {question_id:d} 的已選答案應為 "{answer}"')
def step_impl(context, question_id, answer):
    response = context.last_response
    data = response.json()

    # Find the answer in the response answers list
    answers = data.get("answers", [])
    found = None
    for a in answers:
        # question_id in response might be UUID string
        q_id = a.get("question_id", "")
        if str(question_id) in q_id or q_id.endswith(f"-{question_id:012d}"):
            found = a
            break

    # Try matching by int-based UUID
    import uuid
    target_uuid = str(uuid.UUID(int=question_id))
    if not found:
        for a in answers:
            if a.get("question_id") == target_uuid:
                found = a
                break

    assert found is not None, \
        f"找不到題目 {question_id} 的作答記錄，回傳答案: {answers}"
    assert found.get("selected_answer") == answer, \
        f"預期已選答案為 '{answer}'，實際為 '{found.get('selected_answer')}'"
