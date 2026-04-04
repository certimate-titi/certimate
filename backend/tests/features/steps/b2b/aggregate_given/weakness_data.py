"""Given 群組 N 的班級弱點分析顯示 X 掌握率最低 — Aggregate Given"""

from behave import given, use_step_matcher

use_step_matcher("re")


@given(r'群組 (?P<group_id>\d+) 的班級弱點分析顯示 "(?P<topic>[^"]+)" 掌握率最低（(?P<rate>\d+)%）')
def step_impl(context, group_id, topic, rate):
    """Store weakness data in memo for remediation exam generation."""
    context.memo[f"group_{group_id}_weakest_topic"] = topic
    context.memo[f"group_{group_id}_weakest_rate"] = int(rate)


use_step_matcher("parse")
