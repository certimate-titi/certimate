"""Given 系統中有以下備考科目 — Aggregate Given"""

import uuid

from behave import given

from app.models.subject import SubjectCategory, Subject
from app.repositories.subject_repository import SubjectRepository, SubjectCategoryRepository


@given('系統中有以下備考科目：')
def step_impl(context):
    db = context.db_session
    cat_repo = SubjectCategoryRepository(db)
    subj_repo = SubjectRepository(db)

    # 建立預設分類
    category = SubjectCategory(name="預設分類", sort_order=0)
    category = cat_repo.save(category)

    for row in context.table:
        subject_id = uuid.UUID(int=int(row['科目 ID']))
        subject = Subject(
            id=subject_id,
            category_id=category.id,
            name=row['名稱'],
        )
        subject = subj_repo.save(subject)
        # 以名稱作為 key 存入 context.ids
        context.ids[row['名稱']] = str(subject.id)
