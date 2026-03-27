from behave import given
from app.models.subject import SubjectCategory, Subject


@given('系統中預設存在 "{subject1}" 與 "{subject2}" 兩個學科庫')
def subject_library(context, subject1, subject2):
    db = context.db_session

    # 建立預設分類
    category = db.query(SubjectCategory).first()
    if category is None:
        category = SubjectCategory(name="IT")
        db.add(category)
        db.commit()
        db.refresh(category)

    for name in [subject1, subject2]:
        subject = db.query(Subject).filter_by(name=name).first()
        if not subject:
            subject = Subject(name=name, category_id=category.id)
            db.add(subject)
            db.commit()
            db.refresh(subject)
        context.ids[f"subject_{name}"] = str(subject.id)
