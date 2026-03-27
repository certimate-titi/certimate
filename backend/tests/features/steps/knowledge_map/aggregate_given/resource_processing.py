from behave import given
from app.models.resource import Resource, ResourceType, ResourceStatus
from app.models.subject import Subject
from app.models.learning_journey import LearningJourney


STATUS_MAP = {
    "PENDING": ResourceStatus.PENDING,
    "PROCESSING": ResourceStatus.PROCESSING,
    "COMPLETED": ResourceStatus.COMPLETED,
    "COMPLETED_NO_MAP": ResourceStatus.COMPLETED_NO_MAP,
    "FAILED": ResourceStatus.FAILED,
}


@given('使用者 "{email}" 已上傳 PDF 資源 "{filename}" 且狀態為 "{status}"')
def step_impl(context, email, filename, status):
    db = context.db_session
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    # 取得第一個 subject（預設 AWS SAA）
    subject = db.query(Subject).first()
    assert subject is not None, "系統中尚無學科，請先建立學科庫"

    # 確保有學習歷程
    journey = db.query(LearningJourney).filter_by(
        user_id=user_id, subject_id=subject.id
    ).first()
    if journey is None:
        journey = LearningJourney(user_id=user_id, subject_id=subject.id)
        db.add(journey)
        db.commit()

    resource = Resource(
        user_id=user_id,
        subject_id=subject.id,
        name=filename,
        type=ResourceType.PDF,
        status=STATUS_MAP.get(status, ResourceStatus.PENDING),
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)

    context.ids["last_resource_id"] = str(resource.id)
    context.memo["last_resource"] = resource
