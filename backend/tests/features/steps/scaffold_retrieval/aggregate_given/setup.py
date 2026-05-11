"""Given setup — Feature 37 BDD."""

import uuid

from behave import given

from app.models.resource import Resource
from app.models.resource_scaffold import ResourceScaffold


def _ensure_user(db, email: str):
    """建用戶。"""
    from app.models.user import SubscriptionPlan, User, UserRole, UserStatus

    user = db.query(User).filter_by(email=email).first()
    if user is None:
        user = User(
            email=email,
            password_hash="test-hash",
            subscription_plan=SubscriptionPlan.PRO,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        db.flush()
    return user.id


def _ensure_subject(db):
    from app.models.subject import Subject, SubjectCategory
    cat = db.query(SubjectCategory).first() or SubjectCategory(name="IT")
    if cat.id is None:
        db.add(cat); db.flush()
    subj = db.query(Subject).filter_by(name="F37-subject").first()
    if subj is None:
        subj = Subject(name="F37-subject", category_id=cat.id)
        db.add(subj); db.flush()
    return subj.id


@given('用戶 "{email}" 擁有資源 "{res_name}" 且解析狀態為 "{status_label}"')
def step_user_has_resource_with_status(context, email, res_name, status_label):
    db = context.db_session
    if not hasattr(context, "ids"):
        context.ids = {}
    if email not in context.ids:
        context.ids[email] = str(_ensure_user(db, email))
    user_id = uuid.UUID(context.ids[email])
    subject_id = _ensure_subject(db)

    res = Resource(
        user_id=user_id,
        subject_id=subject_id,
        name=res_name,
        type="pdf",
        status="COMPLETED" if status_label == "success" else status_label.upper(),
        file_size_bytes=1024,
        gcs_path=f"{res_name}.pdf",
        parsed_markdown="# F37 內文",
        detected_content_type="study_material",
    )
    db.add(res)
    db.flush()
    db.commit()
    context.memo["resources"] = context.memo.get("resources", {})
    context.memo["resources"][res_name] = res
    context.memo["last_resource_id"] = str(res.id)
    context.memo["last_user_id"] = user_id


@given('資源 "{res_name}" 含章節 "{chapter}" 對應 page_start={pstart:d} / page_end={pend:d}')
def step_resource_chapter_pages(context, res_name, chapter, pstart, pend):
    """Background 設定章節 page range — 暫存 memo 並建一筆 anchor scaffold
    讓 chapter-practice endpoint 能查到 page_start/page_end。"""
    context.memo["chapters"] = context.memo.get("chapters", {})
    context.memo["chapters"][chapter] = {"page_start": pstart, "page_end": pend}
    # 建一筆 anchor scaffold 帶 page_start/page_end（chapter-practice endpoint 用此查 page range）
    db = context.db_session
    res = _get_resource(context, res_name)
    if res is None:
        return
    # Anchor scaffold 只為 chapter-practice page_range 查詢用，
    # retrieval_prompt 留 NULL 避免污染 takeaway assertion
    sf = ResourceScaffold(
        resource_id=res.id,
        tenant_id=res.tenant_id,
        type="strategy",
        content=f"章節 {chapter} 導讀",
        chapter_heading=chapter,
        retrieval_prompt=None,
        template_code="K-06-study",
        page_start=pstart,
        page_end=pend,
    )
    db.add(sf)
    db.commit()


def _get_resource(context, res_name):
    return context.memo.get("resources", {}).get(res_name)


def _chapter_pages(context, chapter):
    return context.memo.get("chapters", {}).get(chapter, {})


@given('資源 "{res_name}" 章節 "{chapter}" 含一筆 takeaway 鷹架')
def step_takeaway_scaffold_with_table(context, res_name, chapter):
    """以 Gherkin datatable 提供 content + retrieval_prompt。"""
    db = context.db_session
    res = _get_resource(context, res_name)
    ranges = _chapter_pages(context, chapter)
    row = context.table[0]
    sf = ResourceScaffold(
        resource_id=res.id,
        tenant_id=res.tenant_id,
        type="takeaway",
        content=row["content"],
        chapter_heading=chapter,
        retrieval_prompt=row.get("retrieval_prompt"),
        template_code="K-06-study",
        page_start=ranges.get("page_start"),
        page_end=ranges.get("page_end"),
    )
    db.add(sf)
    db.commit()
    context.memo["last_scaffold_id"] = sf.id


@given('資源 "{res_name}" 章節 "{chapter}" 含一筆 strategy 鷹架')
def step_strategy_scaffold(context, res_name, chapter):
    db = context.db_session
    res = _get_resource(context, res_name)
    ranges = _chapter_pages(context, chapter)
    sf = ResourceScaffold(
        resource_id=res.id,
        tenant_id=res.tenant_id,
        type="strategy",
        content="策略提示：先看圖表再讀文字。",
        chapter_heading=chapter,
        retrieval_prompt=None,
        template_code="K-06-study",
        page_start=ranges.get("page_start"),
        page_end=ranges.get("page_end"),
    )
    db.add(sf)
    db.commit()


@given('資源 "{res_name}" 含一筆 takeaway 鷹架 id="{label}"')
def step_takeaway_with_label(context, res_name, label):
    db = context.db_session
    res = _get_resource(context, res_name)
    sf = ResourceScaffold(
        resource_id=res.id,
        tenant_id=res.tenant_id,
        type="takeaway",
        content=f"{label} content",
        chapter_heading="3.1 人工智慧概念",
        retrieval_prompt="想想看",
        template_code="K-06-study",
    )
    db.add(sf)
    db.commit()
    context.memo["scaffold_aliases"] = context.memo.get("scaffold_aliases", {})
    context.memo["scaffold_aliases"][label] = sf.id
    context.memo["last_scaffold_id"] = sf.id


@given('章節 "{chapter}" 對應 scaffold 的 page_start 為 NULL')
def step_chapter_null_page(context, chapter):
    """新增 chapter 但 page_start/end 為 NULL（透過建一筆無頁碼 scaffold 代表）。"""
    db = context.db_session
    # 找 last resource
    res_name = next(iter(context.memo.get("resources", {})))
    res = _get_resource(context, res_name)
    sf = ResourceScaffold(
        resource_id=res.id,
        tenant_id=res.tenant_id,
        type="takeaway",
        content=f"{chapter} 內容",
        chapter_heading=chapter,
        retrieval_prompt=None,
        template_code="K-06-study",
        page_start=None,
        page_end=None,
    )
    db.add(sf)
    db.commit()


@given('已存在另一用戶 "{email}"')
def step_another_user(context, email):
    db = context.db_session
    if not hasattr(context, "ids"):
        context.ids = {}
    if email not in context.ids:
        context.ids[email] = str(_ensure_user(db, email))
    db.commit()


@given('資源 "{res_name}" 在 page {pstart:d}-{pend:d} 範圍內有 {n:d} 題已核可題目')
def step_resource_has_n_questions_in_page_range(context, res_name, pstart, pend, n):
    """建 n 筆 Question + QuestionCandidate（APPROVED，source_page 在 range）。

    chapter-practice endpoint 流程：
      取 QuestionCandidate decision=APPROVED + source_page 在 page_range 內
      → 用 question_text 比對 Question.content。
    """
    from app.models.question import Question
    from app.models.question_candidate import (
        QuestionCandidate, QuestionCandidateDecision, QuestionCandidateTier,
    )

    db = context.db_session
    res = _get_resource(context, res_name)
    for i in range(n):
        content = f"Q{i+1} 內容文字"
        # Question
        q = Question(
            question_number=i + 1,
            content=content,
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_answer="A",
            source_resource_id=res.id,
        )
        db.add(q)
        # 對應 candidate（APPROVED，source_page 在 range）
        cand = QuestionCandidate(
            resource_id=res.id,
            tenant_id=res.tenant_id,
            question_text=content,
            options=["A", "B", "C", "D"],
            source_page=pstart + (i % max(1, pend - pstart + 1)),
            tier=QuestionCandidateTier.T2.value,
            decision=QuestionCandidateDecision.APPROVED.value,
        )
        db.add(cand)
    db.commit()
