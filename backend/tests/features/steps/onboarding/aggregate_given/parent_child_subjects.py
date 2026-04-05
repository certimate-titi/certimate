"""Given 系統中有科目及其子科目 — Aggregate Given"""

from behave import given

from app.models.subject import Subject, SubjectCategory


@given('系統中有科目 "{parent_name}" 及其子科目 "{child_name}"')
def step_impl(context, parent_name, child_name):
    db = context.db_session

    # Ensure category
    cat = db.query(SubjectCategory).first()
    if not cat:
        cat = SubjectCategory(name="default")
        db.add(cat)
        db.flush()

    # Ensure parent subject
    parent = db.query(Subject).filter_by(name=parent_name).first()
    if not parent:
        parent = Subject(name=parent_name, category_id=cat.id, available_questions=0)
        db.add(parent)
        db.flush()

    # Ensure child subject
    child = db.query(Subject).filter_by(name=child_name).first()
    if not child:
        child = Subject(name=child_name, category_id=cat.id, available_questions=100)
        db.add(child)
        db.flush()

    db.commit()
