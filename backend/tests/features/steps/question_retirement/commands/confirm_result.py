"""When 使用者確認考試結果 — Command"""

import uuid

from behave import when
from app.repositories.learning_journey_repository import LearningJourneyRepository
from app.repositories.subject_repository import SubjectRepository


def _get_journey_id(context, email, subject_name):
    """取得學習歷程 ID"""
    key = f"learning_journey_{email}_{subject_name}"
    if key in context.memo:
        return context.memo[key]

    # 嘗試從 DB 查詢
    user_id = uuid.UUID(context.ids[email])
    db = context.db_session
    subject_repo = SubjectRepository(db)
    subject = subject_repo.find_by_name(subject_name)
    lj_repo = LearningJourneyRepository(db)
    journey = lj_repo.find_by_user_and_subject(user_id, subject.id)
    if journey:
        return str(journey.id)
    return None


@when('使用者 "{email}" 確認科目 "{subject_name}" 考試結果為「考取」')
def step_confirm_passed(context, email, subject_name):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    journey_id = _get_journey_id(context, email, subject_name)

    response = context.api_client.post(
        f"/api/v1/learning-journeys/{journey_id}/exam-result",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "passed"},
    )
    context.last_response = response
    context.memo["confirm_email"] = email
    context.memo["confirm_subject"] = subject_name


@when('使用者 "{email}" 確認科目 "{subject_name}" 考試結果為「未考取」')
def step_confirm_failed(context, email, subject_name):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    journey_id = _get_journey_id(context, email, subject_name)

    response = context.api_client.post(
        f"/api/v1/learning-journeys/{journey_id}/exam-result",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "failed"},
    )
    context.last_response = response
    context.memo["confirm_email"] = email
    context.memo["confirm_subject"] = subject_name


@when('使用者選擇「再次報考」並設定：')
def step_retake(context):
    email = context.memo.get("confirm_email")
    subject_name = context.memo.get("confirm_subject")
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    journey_id = _get_journey_id(context, email, subject_name)

    # 解析 DataTable
    fields = {}
    for row in context.table:
        fields[row["欄位"]] = row["值"]

    response = context.api_client.post(
        f"/api/v1/learning-journeys/{journey_id}/retake",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "exam_date": fields.get("新考試日期"),
            "result_date": fields.get("新放榜日期"),
        },
    )
    context.last_response = response


@when('使用者選擇「不再報考」')
def step_quit(context):
    email = context.memo.get("confirm_email")
    subject_name = context.memo.get("confirm_subject")
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    journey_id = _get_journey_id(context, email, subject_name)

    response = context.api_client.post(
        f"/api/v1/learning-journeys/{journey_id}/quit",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者修改放榜日期為 "{date}"')
def step_update_result_date(context, date):
    email = context.memo.get("confirm_email", "alice@example.com")
    user_id = context.ids.get(email)
    if not user_id:
        # 嘗試從已有 journey 取得
        for k, v in context.ids.items():
            if "@" in k:
                user_id = v
                email = k
                break

    token = context.jwt_helper.generate_token(user_id)
    journey_id = context.memo.get("current_journey_id")

    response = context.api_client.put(
        f"/api/v1/learning-journeys/{journey_id}/result-date",
        headers={"Authorization": f"Bearer {token}"},
        json={"result_date": date},
    )
    context.last_response = response
