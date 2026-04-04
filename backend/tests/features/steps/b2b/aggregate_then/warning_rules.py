"""Then 機構的預警規則驗證 — Aggregate Then"""

import uuid
from decimal import Decimal

from behave import then, use_step_matcher

from app.models.early_warning_rule import EarlyWarningRule

use_step_matcher("re")


@then(r'機構 (?P<inst_id>\d+) 的預警規則應為：')
def step_impl(context, inst_id):
    db = context.db_session
    inst_uuid = uuid.UUID(int=int(inst_id))
    rule = db.query(EarlyWarningRule).filter_by(institution_id=inst_uuid).first()
    assert rule is not None, f"找不到機構 {inst_id} 的預警規則"

    for row in context.table:
        field = row["欄位"]
        expected = row["值"]

        if field == "min_avg_score":
            actual = float(rule.min_avg_score)
            assert actual == float(expected), \
                f"{field}: 預期 {expected}，實際 {actual}"
        elif field == "max_decline_trend":
            assert rule.max_decline_trend == int(expected), \
                f"{field}: 預期 {expected}，實際 {rule.max_decline_trend}"
        elif field == "max_inactive_days":
            assert rule.max_inactive_days == int(expected), \
                f"{field}: 預期 {expected}，實際 {rule.max_inactive_days}"


use_step_matcher("parse")
