"""Given 該題 expires_at 已過期 — Aggregate Given"""

import uuid
from datetime import datetime, timedelta, timezone

from behave import given
from app.models.question import Question


@given('該題 expires_at 已過期')
def step_impl(context):
    db = context.db_session
    question_id = uuid.UUID(context.memo["current_question_id"])

    q = db.query(Question).filter_by(id=question_id).first()
    q.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.commit()
