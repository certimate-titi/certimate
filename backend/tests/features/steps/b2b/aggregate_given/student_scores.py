"""Given 學員 N 最近三次測驗平均分為 X — Aggregate Given"""

import uuid

from behave import given, use_step_matcher

use_step_matcher("re")


@given(r'學員 "(?P<email>[^"]+)" 最近三次測驗平均分為 (?P<score>\d+)')
def step_impl(context, email, score):
    """Store student score in memo for early warning checks."""
    user_id = context.ids[email]
    context.memo[f"student_avg_score_{user_id}"] = int(score)
    context.memo[f"student_email_{user_id}"] = email
    # Also store by email for easy lookup
    context.memo[f"student_avg_score_by_email_{email}"] = int(score)


use_step_matcher("parse")
