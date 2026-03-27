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


@given('使用者 "{email}" 已提交 YouTube URL 且狀態為 "{status}"')
def step_impl(context, email, status):
    db = context.db_session
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    subject = db.query(Subject).first()
    assert subject is not None, "系統中尚無學科，請先建立學科庫"

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
        name="YouTube 影片",
        type=ResourceType.YOUTUBE,
        status=STATUS_MAP.get(status, ResourceStatus.PENDING),
        youtube_url="https://www.youtube.com/watch?v=test123",
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)

    context.ids["last_resource_id"] = str(resource.id)
    context.memo["last_resource"] = resource
