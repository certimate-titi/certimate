"""Given 使用者擁有 personal subject（無 LearningJourney）— Aggregate Given

測試 owner bypass：subject owner 不需 LearningJourney 亦可讀取自己 subject 的 nodes。
"""

import uuid

from behave import given

from app.models.subject import Subject, SubjectCategory
from app.repositories.subject_repository import SubjectRepository, SubjectCategoryRepository


@given('使用者 "{email}" 擁有 personal subject "{subject_name}"（無 LearningJourney）')
def step_impl(context, email, subject_name):
    """建立 scope='personal'、owner_user_id=user 的 subject，刻意不建 LearningJourney。"""
    db = context.db_session

    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    owner_id = uuid.UUID(context.ids[email])

    cat_repo = SubjectCategoryRepository(db)
    subj_repo = SubjectRepository(db)

    # 取得或建立預設分類
    category = SubjectCategory(name="個人分類", sort_order=0)
    category = cat_repo.save(category)

    subject = Subject(
        category_id=category.id,
        name=subject_name,
        owner_user_id=owner_id,
        scope="personal",
    )
    subject = subj_repo.save(subject)
    # 記錄 subject name → id
    context.ids[subject_name] = str(subject.id)
    # 刻意不建立 LearningJourney — 這是 bug 根因的測試場景
