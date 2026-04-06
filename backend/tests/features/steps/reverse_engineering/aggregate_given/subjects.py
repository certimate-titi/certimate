"""Given 系統中有以下考科 — Aggregate Given"""

import uuid

from behave import given

from app.models.subject import Subject
from app.repositories.subject_repository import SubjectRepository


@given('系統中有以下考科：')
def step_impl(context):
    db = context.db_session
    repo = SubjectRepository(db)

    for row in context.table:
        cat_id_key = f"cat_{row['分類 ID']}"
        if cat_id_key not in context.ids:
            # Auto-create category if not found
            from app.models.subject import SubjectCategory
            from app.repositories.subject_repository import SubjectCategoryRepository
            cat_repo = SubjectCategoryRepository(db)
            cat = SubjectCategory(name=f"自動分類_{row['分類 ID']}")
            saved_cat = cat_repo.save(cat)
            context.ids[cat_id_key] = str(saved_cat.id)

        category_id = uuid.UUID(context.ids[cat_id_key])
        is_popular = row.get("is_popular", "false").lower() in ("true", "1", "yes")

        subject = Subject(
            category_id=category_id,
            name=row["名稱"],
            is_popular=is_popular,
        )
        saved = repo.save(subject)
        context.ids[f"subject_{row['考科 ID']}"] = str(saved.id)
        context.ids[f"subject_name_{row['名稱']}"] = str(saved.id)
