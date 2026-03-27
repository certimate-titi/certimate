from behave import given
from app.models.resource import Resource, ResourceType, ResourceStatus
from app.models.subject import Subject
from app.models.learning_journey import LearningJourney


@given('使用者 "{email}" 上傳了僅含 {lines:d} 行文字的 PDF')
def step_impl(context, email, lines):
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
        name=f"short_content_{lines}_lines.pdf",
        type=ResourceType.PDF,
        status=ResourceStatus.PROCESSING,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)

    context.ids["last_resource_id"] = str(resource.id)
    context.memo["last_resource"] = resource
    context.memo["short_content_lines"] = lines
