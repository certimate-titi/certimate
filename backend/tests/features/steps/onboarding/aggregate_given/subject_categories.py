"""Given 系統中有以下證照科目分類 — Aggregate Given"""

from behave import given

from app.models.subject import SubjectCategory, Subject


@given('系統中有以下證照科目分類：')
def step_impl(context):
    db = context.db_session

    for row in context.table:
        category_name = row["分類"]
        examples_raw = row["科目範例"]

        cat = SubjectCategory(name=category_name)
        db.add(cat)
        db.flush()
        context.ids[f"cat_{category_name}"] = str(cat.id)

        # Parse subjects separated by 、
        subject_names = [s.strip() for s in examples_raw.split("、") if s.strip()]
        for sname in subject_names:
            subj = Subject(name=sname, category_id=cat.id)
            db.add(subj)
            db.flush()
            context.ids[f"subject_{sname}"] = str(subj.id)

    db.commit()
