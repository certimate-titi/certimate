"""Given 系統中有以下學員群組 — Aggregate Given"""

import uuid

from behave import given

from app.models.student_group import StudentGroup


@given('系統中有以下學員群組：')
def step_impl(context):
    db = context.db_session

    for row in context.table:
        group_id = int(row["群組 ID"])
        inst_id = int(row["機構 ID"])
        name = row["名稱"]

        group = StudentGroup(
            id=uuid.UUID(int=group_id),
            institution_id=uuid.UUID(int=inst_id),
            name=name,
        )
        db.add(group)
        db.flush()
        context.ids[f"group_{group_id}"] = str(group.id)

    db.commit()
