"""Then 增量逆向工程保留既有結構 — Aggregate Then"""

import uuid

from behave import then

from app.models.knowledge_node import KnowledgeNode
from app.models.question import Question
from app.models.exam import Exam


@then('系統應保留既有節點結構')
def step_impl(context):
    db = context.db_session

    # Verify previously created nodes still exist
    for key, val in context.ids.items():
        if key.startswith("node_"):
            node = db.query(KnowledgeNode).filter_by(id=uuid.UUID(val)).first()
            assert node is not None, \
                f"預期既有節點 '{key}' 仍存在，但已被刪除"


@then('新題目應被映射到現有或新增的知識節點')
def step_impl_mapped(context):
    db = context.db_session

    # Find subject from context
    subject_id = None
    for key, val in context.ids.items():
        if key.startswith("subject_name_"):
            subject_id = uuid.UUID(val)
            break
    assert subject_id, "找不到任何考科"

    # Check that questions have node_id set
    unmapped = (
        db.query(Question)
        .join(Exam, Question.exam_id == Exam.id)
        .filter(Exam.subject_id == subject_id, Question.node_id.is_(None))
        .count()
    )
    total = (
        db.query(Question)
        .join(Exam, Question.exam_id == Exam.id)
        .filter(Exam.subject_id == subject_id)
        .count()
    )
    assert unmapped == 0, \
        f"預期所有題目已映射，但有 {unmapped}/{total} 題未映射"


@then('出題頻率統計應更新')
def step_impl_freq_updated(context):
    db = context.db_session

    # Find subject from context
    subject_id = None
    for key, val in context.ids.items():
        if key.startswith("subject_name_"):
            subject_id = uuid.UUID(val)
            break
    assert subject_id, "找不到任何考科"

    nodes_with_freq = (
        db.query(KnowledgeNode)
        .filter(
            KnowledgeNode.subject_id == subject_id,
            KnowledgeNode.exam_frequency.isnot(None),
        )
        .count()
    )
    assert nodes_with_freq > 0, \
        "預期至少有一個節點的 exam_frequency 已設定"
