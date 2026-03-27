"""Given 系統中有以下意見反饋紀錄 — Aggregate Given"""

from datetime import datetime, timezone

from behave import given

from app.models.feedback import Feedback


@given('系統中有以下意見反饋紀錄：')
def step_impl(context):
    db = context.db_session

    for row in context.table:
        user_id_key = row["使用者 ID"]
        user_uuid = context.ids.get(user_id_key)
        assert user_uuid is not None, f"找不到使用者 ID '{user_id_key}' 對應的 UUID"

        created_at = datetime.fromisoformat(row["建立時間"]).replace(tzinfo=timezone.utc)

        feedback = Feedback(
            feedback_id=row["反饋 ID"],
            user_id=user_uuid,
            type=row["類型"],
            subject=row["主旨"],
            content=f"測試反饋內容 - {row['反饋 ID']}",
            status=row["狀態"],
            created_at=created_at,
            admin_reply="管理員已回覆此問題" if row["狀態"] == "RESOLVED" else None,
            resolved_at=created_at if row["狀態"] == "RESOLVED" else None,
        )
        db.add(feedback)
        db.flush()

        context.ids[row["反饋 ID"]] = str(feedback.id)

    db.commit()
