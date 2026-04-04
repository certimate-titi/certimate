"""Given 系統中有以下早期預警規則 — Aggregate Given"""

import uuid
from decimal import Decimal

from behave import given, use_step_matcher

from app.models.early_warning_rule import EarlyWarningRule

use_step_matcher("re")


@given(r'系統中有以下早期預警規則（機構 (?P<inst_id>\d+)）：')
def step_impl(context, inst_id):
    db = context.db_session
    inst_uuid = uuid.UUID(int=int(inst_id))

    for row in context.table:
        rule = EarlyWarningRule(
            institution_id=inst_uuid,
            min_avg_score=Decimal(row["最低平均分"]),
            max_decline_trend=int(row["最大連續下降次數"]),
            max_inactive_days=int(row["最大未登入天數"]),
        )
        db.add(rule)

    db.flush()
    db.commit()


use_step_matcher("parse")
