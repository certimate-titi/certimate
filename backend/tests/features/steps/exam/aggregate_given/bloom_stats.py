"""Given 學科有以下考古題 Bloom 統計 — Aggregate Given"""

import json
import uuid

from behave import given

from app.models.resource import Resource
from app.models.subject import Subject, SubjectCategory
from app.repositories.subject_repository import SubjectRepository, SubjectCategoryRepository


@given('學科 "{subject_name}" 有以下考古題 Bloom 統計：')
def step_impl(context, subject_name):
    db = context.db_session
    subject_repo = SubjectRepository(db)
    cat_repo = SubjectCategoryRepository(db)

    # 建立或取得學科
    subject = subject_repo.find_by_name(subject_name)
    if not subject:
        if "bloom_cat" not in context.ids:
            cat = SubjectCategory(name="Bloom 測試分類")
            cat_repo.save(cat)
            context.ids["bloom_cat"] = str(cat.id)
        cat_id = uuid.UUID(context.ids["bloom_cat"])
        subject = Subject(name=subject_name, category_id=cat_id)
        subject_repo.save(subject)

    context.ids[f"subject_{subject_name}"] = str(subject.id)

    # 將 Bloom 統計存到 memo
    bloom_stats = {}
    for row in context.table:
        bloom_stats[row["bloom_category"]] = int(row["percentage"])

    if "bloom_stats" not in context.memo:
        context.memo["bloom_stats"] = {}
    context.memo["bloom_stats"][subject_name] = bloom_stats

    # 將 Bloom 統計存到 Subject.description（讓 API 可偵測）
    subject.description = json.dumps({"bloom_stats": bloom_stats})
    subject.available_questions = sum(bloom_stats.values())
    db.commit()

    # 更新所有資源的 subject_id 到此學科（讓 API 可透過 resource → subject 找到 bloom stats）
    db.query(Resource).update({"subject_id": subject.id})
    db.commit()
