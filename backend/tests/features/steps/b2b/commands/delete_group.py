"""When 使用者刪除群組 — Command (DELETE)"""
import uuid as _uuid

from behave import when, use_step_matcher

use_step_matcher("re")


@when(r'使用者 "(?P<email>[^"]+)" 刪除機構 (?P<inst_id>\d+) 的群組 "(?P<group_name>[^"]+)"')
def step_delete_group(context, email, inst_id, group_name):
    """DELETE /api/v1/b2b/groups/{group_id}"""
    from app.models.student_group import StudentGroup

    # Resolve institution UUID
    actual_inst_id = context.ids.get(
        f"institution_{inst_id}", str(_uuid.UUID(int=int(inst_id)))
    )
    group = context.db_session.query(StudentGroup).filter_by(
        institution_id=_uuid.UUID(actual_inst_id),
        name=group_name,
    ).first()
    group_id = str(group.id) if group else str(_uuid.UUID(int=0))

    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    context.last_response = context.api_client.delete(
        f"/api/v1/b2b/groups/{group_id}",
        headers={"Authorization": f"Bearer {token}"},
    )


use_step_matcher("parse")
