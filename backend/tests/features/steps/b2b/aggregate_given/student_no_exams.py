"""Given 學員尚未完成任何考試（空狀態） — Aggregate Given"""

from behave import given, use_step_matcher

use_step_matcher("re")


@given(r'學員 "(?P<email>[^"]+)" 尚未完成任何考試')
def step_impl(context, email):
    """Ensure no exam records exist for the student (no-op, just documentation)."""
    # No action needed — the student simply has no exam records
    pass


use_step_matcher("parse")
