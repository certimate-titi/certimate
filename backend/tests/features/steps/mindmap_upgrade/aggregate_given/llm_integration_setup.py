"""Given — LLM-integration scenario 前置資料建立 (mindmap upgrade Feature 34).

這些 step 負責建立 @llm-integration 標籤 Scenario 所需的 DB 資料，
並對 _call_gemini_inner 注入 mock，避免測試環境觸發真實 Gemini API。
"""

import uuid

from behave import given

from app.models.knowledge_node import KnowledgeNode
from app.models.subject import Subject, SubjectCategory
from app.models.syllabus_topic import SyllabusTopic
from app.models.historical_exam import HistoricalExam
from app.models.question import Question


def _ensure_subject(db, subject_name: str) -> uuid.UUID:
    subj = db.query(Subject).filter(Subject.name == subject_name).first()
    if subj:
        return subj.id
    cat = db.query(SubjectCategory).first()
    if cat is None:
        cat = SubjectCategory(name="BDD Category")
        db.add(cat)
        db.flush()
    subj = Subject(name=subject_name, category_id=cat.id)
    db.add(subj)
    db.flush()
    return subj.id


# ─── Scenario 1: syllabus_topics + extract ───────────────────────────────────

CHAPTER_NAMES = [
    "資訊安全概論",
    "存取控制與身份驗證",
    "密碼學",
    "網路安全",
    "應用程式安全",
    "資安法規與標準",
]


@given('系統有一個科目 "{subject_name}" 含 {n:d} 個 syllabus_topics 章節')
def step_impl_subject_with_syllabus(context, subject_name, n):
    """建立科目並植入 n 個 syllabus_topics 根節點（depth=0）。"""
    db = context.db_session
    sid = _ensure_subject(db, subject_name)
    context.memo["llm_subject_id"] = str(sid)
    context.memo["llm_subject_name"] = subject_name

    chapter_list = CHAPTER_NAMES[:n]
    context.memo["syllabus_chapter_names"] = chapter_list

    for i, ch_name in enumerate(chapter_list):
        topic = SyllabusTopic(
            subject_id=sid,
            name=ch_name,
            depth=0,
            weight=1.0,
            is_active=True,
        )
        db.add(topic)
    db.commit()


@given('該科目有 {n:d} 題考古題')
def step_impl_subject_has_exam_questions(context, n):
    """為 llm_subject_id 建立 n 題歷史考古題（不分節點）。"""
    db = context.db_session
    sid = uuid.UUID(context.memo["llm_subject_id"])
    subject_name = context.memo["llm_subject_name"]

    exam = HistoricalExam(
        exam_code="BDD",
        category_code="LLM",
        subject_code="SECU",
        exam_name=subject_name,
        subject_name=subject_name,
        total_questions=n,
    )
    db.add(exam)
    db.flush()

    for i in range(1, n + 1):
        q = Question(
            historical_exam_id=exam.id,
            question_number=i,
            content=f"資訊安全考題 {i}",
            option_a="A",
            option_b="B",
            option_c="C",
            option_d="D",
            correct_answer="A",
        )
        db.add(q)
    db.commit()
    context.memo["llm_exam_id"] = str(exam.id)


# ─── Scenario 2: weak-keyword voyage semantic fallback ───────────────────────

@given('系統有一個科目含 {total_q:d} 題考古題和 {n_nodes:d} 個知識節點')
def step_impl_subject_with_q_and_nodes(context, total_q, n_nodes):
    """建立科目 + N 個知識節點 + total_q 題考古題。"""
    db = context.db_session
    sid = _ensure_subject(db, "BDD Voyage Fallback")
    context.memo["voyage_subject_id"] = str(sid)

    node_names = [f"節點{i+1}" for i in range(n_nodes)]
    node_ids = []
    for i, name in enumerate(node_names):
        node = KnowledgeNode(subject_id=sid, name=name, depth=1, sort_order=i)
        db.add(node)
        db.flush()
        node_ids.append(str(node.id))
    context.memo["voyage_node_ids"] = node_ids
    context.memo["voyage_node_names"] = node_names

    exam = HistoricalExam(
        exam_code="BDD",
        category_code="VY",
        subject_code="VOY",
        exam_name="BDD Voyage Fallback",
        subject_name="BDD Voyage Fallback",
        total_questions=total_q,
    )
    db.add(exam)
    db.flush()

    # First (total_q - 5) questions contain node keywords; last 5 are weak
    strong_count = total_q - 5
    for i in range(1, total_q + 1):
        if i <= strong_count:
            content = f"關於 節點{((i-1) % n_nodes) + 1} 的問題 {i}"
        else:
            content = f"抽象概念問題 {i}（無明確關鍵字）"
        q = Question(
            historical_exam_id=exam.id,
            question_number=i,
            content=content,
            option_a="A",
            option_b="B",
            option_c="C",
            option_d="D",
            correct_answer="A",
        )
        db.add(q)
    db.commit()
    context.memo["voyage_total_q"] = total_q
    context.memo["voyage_exam_id"] = str(exam.id)


@given('其中 {n:d} 題的題幹不包含任何節點關鍵字')
def step_impl_weak_keyword_questions(context, n):
    """驗證已在前一步建立弱 keyword 題目（context assertion）。"""
    # Questions were pre-created in the previous step with weak keywords.
    context.memo["voyage_weak_q_count"] = n


# ─── Scenario 3: extract with any subject ────────────────────────────────────

@given('系統對某科目執行 extract()')
def step_impl_run_extract_any_subject(context):
    """建立最小科目 + 考古題，用 mock _call_gemini_inner 執行 extract()。"""
    from unittest.mock import patch
    db = context.db_session
    sid = _ensure_subject(db, "BDD QA Gate Subject")

    exam = HistoricalExam(
        exam_code="BDD",
        category_code="QG",
        subject_code="GATE",
        exam_name="BDD QA Gate Subject",
        subject_name="BDD QA Gate Subject",
        total_questions=3,
    )
    db.add(exam)
    db.flush()
    for i in range(1, 4):
        q = Question(
            historical_exam_id=exam.id,
            question_number=i,
            content=f"測試題 {i}",
            option_a="A",
            option_b="B",
            option_c="C",
            option_d="D",
            correct_answer="A",
        )
        db.add(q)
    db.commit()

    mock_tree = _build_mock_gemini_response(["品質閘門"])

    from app.services import unified_knowledge_extraction_service as ukes_module
    with patch.object(
        ukes_module.UnifiedKnowledgeExtractionService,
        "_call_gemini_inner",
        return_value=mock_tree,
    ):
        from app.services.unified_knowledge_extraction_service import (
            UnifiedKnowledgeExtractionService,
        )
        svc = UnifiedKnowledgeExtractionService(db)
        result = svc.extract(str(sid))

    context.memo["extract_result"] = result


# ─── helpers ─────────────────────────────────────────────────────────────────

def _build_mock_gemini_response(chapter_names: list[str]) -> dict:
    """回傳 UnifiedKnowledgeExtractionService._call_gemini_inner 的最小合法結構。

    Description 長度必須通過 QA gate 的 DESC_MISSING 檢查：
    source_text length >= len(name) + 100 chars。
    章層：source_text = "# {name}\\n\\n{ch_desc}"
    節層：source_text = "# {sec_name}\\n\\n{sec_desc}" + bloom
    """
    _filler = (
        "本章涵蓋核心理論與實務應用，包含基礎概念、適用情境、"
        "判斷原則及常見考題型態。考生應掌握各知識點的定義與相互關係，"
        "並能在情境題中正確判斷最佳處理方式，以達到高效備考目標。"
        "此章節為考試重點，需熟悉各主要技術標準與最佳實踐原則。"
    )  # ~120 chars — enough for any name length
    chapters = [
        {
            "name": name,
            "description": f"{name} {_filler}",
            "sections": [
                {
                    "name": f"{name}-節1",
                    "description": f"{name}-節1 {_filler}",
                    "exam_frequency": "medium",
                    "bloom_levels": ["remember", "understand"],
                }
            ],
        }
        for name in chapter_names
    ]
    return {
        "knowledge_tree": {"chapters": chapters},
        "node_mapping": {},
        "question_keywords": {name: [name] for name in chapter_names},
    }
