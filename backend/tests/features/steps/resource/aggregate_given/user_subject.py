from behave import given
from app.models.subject import SubjectCategory, Subject
from app.models.learning_journey import LearningJourney


@given('使用者 "{email}" 備考科目為 "{subject_name}"（科目 ID: {subject_id:d}）')
def step_impl(context, email, subject_name, subject_id):
    db = context.db_session
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"

    # Create a category if needed
    category = db.query(SubjectCategory).first()
    if category is None:
        category = SubjectCategory(name="IT")
        db.add(category)
        db.commit()
        db.refresh(category)

    # Create subject
    subject = Subject(
        name=subject_name,
        category_id=category.id,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)

    context.ids[f"subject_{subject_id}"] = str(subject.id)

    # Create learning journey
    journey = LearningJourney(
        user_id=user_id,
        subject_id=subject.id,
    )
    db.add(journey)
    db.commit()
