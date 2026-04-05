"""Given 系統中有科目屬於分類 — Aggregate Given"""

import uuid
from behave import given
from app.models.subject import Subject, SubjectCategory


@given('系統中有科目 "{subject_name}" 屬於分類 "{category_name}"')
def step_impl(context, subject_name, category_name):
    db = context.db_session

    # Find or create category
    cat = db.query(SubjectCategory).filter_by(name=category_name).first()
    if not cat:
        cat = SubjectCategory(id=uuid.uuid4(), name=category_name)
        db.add(cat)
        db.flush()

    # Find or create subject
    subj = db.query(Subject).filter_by(name=subject_name).first()
    if not subj:
        subj = Subject(
            id=uuid.uuid4(),
            category_id=cat.id,
            name=subject_name,
            name_en=subject_name,
            is_popular=True,
            available_questions=50,
        )
        db.add(subj)
    else:
        subj.category_id = cat.id
    db.commit()
