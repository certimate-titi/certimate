"""Given 學員能力分析資料建立 — Aggregate Given"""

from behave import given, use_step_matcher

use_step_matcher("re")


@given(r'學員 "(?P<email>[^"]+)" 的能力分析為：')
def step_impl(context, email):
    """Store student competency data in context.memo for mock service."""

    competencies = []
    for row in context.table:
        competencies.append({
            "label": row["知識節點"],
            "score": int(row["分數"]),
        })
    context.memo.setdefault("student_competencies", {})[email] = competencies


use_step_matcher("parse")
