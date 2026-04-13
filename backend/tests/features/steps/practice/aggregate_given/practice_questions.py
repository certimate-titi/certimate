"""Given 知識節點有練習題。"""

import uuid

from behave import given

from app.models.question import Question


def _ensure_practice_exam(context):
    """確保有一個用於練習題的 HistoricalExam（滿足 CHECK 約束）。"""
    if context.memo.get("practice_exam_id"):
        return uuid.UUID(context.memo["practice_exam_id"])

    db = context.db_session
    from app.models.historical_exam import HistoricalExam
    he = HistoricalExam(
        exam_code="PRACTICE",
        exam_name="練習題庫",
        category_code="practice",
        subject_code="practice_general",
    )
    db.add(he)
    db.flush()
    context.memo["practice_exam_id"] = str(he.id)
    return he.id


@given('知識節點 "{node_name}" 有以下練習題：')
def step_impl(context, node_name):
    db = context.db_session

    # 從 context.ids 找到節點
    node_id = None
    for key, val in context.ids.items():
        if key.startswith("node_"):
            from app.models.knowledge_node import KnowledgeNode
            node = db.query(KnowledgeNode).filter(
                KnowledgeNode.id == uuid.UUID(val),
                KnowledgeNode.name == node_name,
            ).first()
            if node:
                node_id = node.id
                break

    assert node_id, f"找不到知識節點 {node_name}"

    historical_exam_id = _ensure_practice_exam(context)

    for row in context.table:
        q_key = row["題目 ID"]
        question = Question(
            node_id=node_id,
            historical_exam_id=historical_exam_id,
            question_number=1,
            type="single_choice",
            difficulty="medium",
            content=row["題目內容"],
            option_a=row["選項A"],
            option_b=row["選項B"],
            option_c=row["選項C"],
            option_d=row["選項D"],
            correct_answer=row["正確答案"],
            explanation=row["詳解"],
        )
        db.add(question)
        db.flush()

        context.ids[f"question_{q_key}"] = str(question.id)

    db.commit()
