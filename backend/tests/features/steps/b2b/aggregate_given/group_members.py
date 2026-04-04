"""Given 群組 N 包含以下學員 — Aggregate Given"""

import uuid

from behave import given, use_step_matcher

from app.models.student_group import StudentGroup, StudentGroupMember
from app.models.user import User

use_step_matcher("re")


@given(r'群組 (?P<group_id>\d+) 包含以下學員：')
def step_impl(context, group_id):
    db = context.db_session
    group_uuid = uuid.UUID(int=int(group_id))

    # Get the group's institution_id to set org_id on students
    group = db.query(StudentGroup).filter_by(id=group_uuid).first()
    institution_id = group.institution_id if group else None

    for row in context.table:
        student_email = row["Email"]
        student_uuid = uuid.UUID(context.ids[student_email])

        member = StudentGroupMember(
            group_id=group_uuid,
            user_id=student_uuid,
        )
        db.add(member)

        # Set org_id on the student user
        if institution_id:
            user = db.query(User).filter_by(id=student_uuid).first()
            if user:
                user.org_id = institution_id

    db.flush()
    db.commit()


use_step_matcher("parse")
