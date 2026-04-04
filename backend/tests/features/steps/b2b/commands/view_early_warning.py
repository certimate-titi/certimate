"""When 使用者查看機構的早期預警清單 — Command (GET)"""

import json

from behave import when, use_step_matcher

use_step_matcher("re")


@when(r'使用者 "(?P<email>[^"]+)" 查看機構 (?P<inst_id>\d+) 的早期預警清單')
def step_impl(context, email, inst_id):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    # Collect any student score overrides from memo
    score_overrides = {}
    for key, val in context.memo.items():
        if key.startswith("student_avg_score_by_email_"):
            student_email = key.replace("student_avg_score_by_email_", "")
            score_overrides[student_email] = val

    params = {}
    if score_overrides:
        params["score_overrides"] = json.dumps(score_overrides)

    response = context.api_client.get(
        f"/api/v1/b2b/institutions/{inst_id}/early-warnings",
        params=params,
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


use_step_matcher("parse")
