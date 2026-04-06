"""Given 系統中有以下考科分類 — Aggregate Given"""

from behave import given

from app.models.subject import SubjectCategory
from app.repositories.subject_repository import SubjectCategoryRepository


@given('系統中有以下考科分類：')
def step_impl(context):
    db = context.db_session
    repo = SubjectCategoryRepository(db)

    for row in context.table:
        cat = SubjectCategory(
            name=row["名稱"],
        )
        saved = repo.save(cat)
        context.ids[f"cat_{row['分類 ID']}"] = str(saved.id)
        context.ids[f"cat_name_{row['名稱']}"] = str(saved.id)
