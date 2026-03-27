"""Given 系統中有以下機構 — Aggregate Given"""

import uuid

from behave import given

from app.models.institution import Institution


@given('系統中有以下機構：')
def step_impl(context):
    db = context.db_session

    for row in context.table:
        inst_id = int(row["機構 ID"])
        name = row["名稱"]
        admin_id_key = row["管理員 ID"].strip()

        admin_uuid = uuid.UUID(context.ids[admin_id_key])

        inst = Institution(
            id=uuid.UUID(int=inst_id),
            name=name,
            admin_user_id=admin_uuid,
        )
        db.add(inst)
        db.flush()
        context.ids[f"institution_{inst_id}"] = str(inst.id)

    db.commit()
