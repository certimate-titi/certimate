"""Given 使用者已上傳資源並完成 LLM 解析 — EPIC-035."""

import uuid
from datetime import datetime, timezone

from behave import given

from app.models.question import Question
from app.models.question_candidate import (
    QuestionCandidate,
    QuestionCandidateDecision,
    QuestionCandidateTier,
)
from app.models.resource import Resource
from app.models.resource_parse_job import ParseJobStatus, ResourceParseJob


@given('使用者 "{email}" 已上傳資源 "{filename}"（科目 ID: {subject_id:d}）並完成 LLM 解析，'
       '包含 {t1:d} 個 T1 題、{t2:d} 個 T2 題、{t3:d} 個 T3 題')
def step_impl(context, email, filename, subject_id, t1, t2, t3):
    db = context.db_session
    user_id = context.ids.get(email)
    assert user_id is not None, f"找不到使用者 '{email}' 的 ID"
    subject_uuid = context.ids.get(f"subject_{subject_id}")
    assert subject_uuid is not None, f"找不到科目 ID {subject_id}"

    resource = Resource(
        user_id=uuid.UUID(user_id),
        name=filename,
        type="pdf",
        status="COMPLETED",
        subject_id=uuid.UUID(subject_uuid),
        file_size_bytes=1024 * 1024,
        parsed_markdown="# LLM 解析內容\n\n段落一。",
        detected_content_type="mixed",
        trust_level=2,
    )
    db.add(resource)
    db.flush()

    job = ResourceParseJob(
        resource_id=resource.id,
        tenant_id=resource.tenant_id,
        status=ParseJobStatus.SUCCESS.value,
        gemini_model="gemini-2.5-pro",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        critical_pages=[1, 3],
        detected_content_type="mixed",
    )
    db.add(job)

    for i in range(t1):
        db.add(Question(
            content=f"T1 題 {i+1}：{filename}",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_answer="A",
            source_resource_id=resource.id,
            owner_user_id=resource.user_id,
            source_type="user_upload",
            tenant_id=resource.tenant_id,
            answer_source="from_source",
            confidence=0.95,
            needs_answer=False,
            never_for_scoring=False,
            question_number=i,
        ))

    for tier, count in (("T2", t2), ("T3", t3)):
        for i in range(count):
            db.add(QuestionCandidate(
                resource_id=resource.id,
                tier=tier,
                question_text=f"{tier} 候選題 {i+1}",
                options=["選項A", "選項B", "選項C", "選項D"],
                ai_inferred_answer="B",
                confidence=0.75 if tier == "T2" else 0.55,
                source_page=i + 1,
                decision=QuestionCandidateDecision.PENDING.value,
            ))

    db.commit()
    db.refresh(resource)
    context.memo["last_resource_id"] = str(resource.id)
