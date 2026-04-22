"""Given 已解析資源附帶鷹架（scaffolds） — EPIC-035 M7 Layer A."""

import uuid

from behave import given

from app.models.resource import Resource
from app.models.resource_scaffold import ResourceScaffold, ResourceScaffoldType
from app.models.subject import Subject, SubjectCategory


_TYPE_MAP = {
    "takeaway": ResourceScaffoldType.TAKEAWAY,
    "elaborative": ResourceScaffoldType.ELABORATIVE,
    "strategy": ResourceScaffoldType.STRATEGY,
}


def _ensure_subject(db) -> uuid.UUID:
    cat = db.query(SubjectCategory).first()
    if cat is None:
        cat = SubjectCategory(name="IT")
        db.add(cat)
        db.flush()
    subj = db.query(Subject).filter_by(name="EPIC-035 Scaffold").first()
    if subj is None:
        subj = Subject(name="EPIC-035 Scaffold", category_id=cat.id)
        db.add(subj)
        db.flush()
    return subj.id


@given('使用者 "{email}" 已上傳資源 "{filename}" 並完成解析，'
       '附帶 {count:d} 筆鷹架（{types}）')
def step_impl(context, email, filename, count, types):
    user_id = uuid.UUID(context.ids[email])
    db = context.db_session

    res = Resource(
        user_id=user_id,
        subject_id=_ensure_subject(db),
        name=filename,
        type="pdf",
        status="COMPLETED",
        file_size_bytes=1024,
        parsed_markdown="# 章節一\n\n內容...",
    )
    db.add(res)
    db.flush()

    type_list = [t.strip() for t in types.split(",")]
    assert len(type_list) == count, f"types 數量 {len(type_list)} 不等於 count {count}"

    scaffolds = []
    for idx, t in enumerate(type_list, start=1):
        s = ResourceScaffold(
            resource_id=res.id,
            chapter_heading=f"章節 {idx}",
            type=_TYPE_MAP[t].value,
            content=f"第 {idx} 筆 {t} 內容",
        )
        db.add(s)
        scaffolds.append(s)
    db.commit()
    for s in scaffolds:
        db.refresh(s)

    context.memo["last_resource_id"] = str(res.id)
    context.memo["last_scaffold_ids"] = [str(s.id) for s in scaffolds]
