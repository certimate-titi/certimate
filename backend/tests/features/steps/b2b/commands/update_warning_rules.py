"""When 使用者更新機構的預警規則 — Command (PUT)"""

from behave import when, use_step_matcher

use_step_matcher("re")


@when(r'使用者 "(?P<email>[^"]+)" 更新機構 (?P<inst_id>\d+) 的預警規則，最低平均分為 (?P<min_score>\d+)，最大連續下降次數為 (?P<max_decline>\d+)，最大未登入天數為 (?P<max_inactive>\d+)')
def step_impl(context, email, inst_id, min_score, max_decline, max_inactive):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.put(
        f"/api/v1/b2b/institutions/{inst_id}/warning-rules",
        json={
            "min_avg_score": int(min_score),
            "max_decline_trend": int(max_decline),
            "max_inactive_days": int(max_inactive),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


use_step_matcher("parse")
