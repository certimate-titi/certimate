"""Given 合併狀態相關前置資料 — Aggregate Given"""

import uuid
from decimal import Decimal

from behave import given

from app.models.exam import Exam
from app.models.knowledge_node import KnowledgeNode
from app.models.merge_history import MergeHistory
from app.models.node_mastery import NodeMastery
from app.models.question import Question


@given('考科 "{subject_name}" 已有 {count:d} 個節點的統一知識樹（考古題 + 教材）')
def step_existing_unified_tree(context, subject_name, count):
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}

    subject_id = uuid.UUID(context.ids[f"subject_name_{subject_name}"])
    context.memo["merge_subject_id"] = str(subject_id)

    # Create placeholder nodes
    for i in range(count):
        source = "exam" if i < count // 2 else "exam,document"
        node = KnowledgeNode(
            subject_id=subject_id,
            name=f"節點_{i+1}",
            depth=1 if i % 3 == 0 else 2,
            sort_order=i,
            source_origin=source,
        )
        db.add(node)
        db.flush()
        context.ids[f"node_節點_{i+1}"] = str(node.id)

    db.commit()
    context.memo["existing_node_count"] = count


@given('考科 "{subject_name}" 已有統一知識樹')
def step_has_unified_tree(context, subject_name):
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}

    subject_id_str = context.ids[f"subject_name_{subject_name}"]
    subject_id = uuid.UUID(subject_id_str)
    context.memo["merge_subject_id"] = subject_id_str

    # Create a few nodes if none exist
    existing = db.query(KnowledgeNode).filter_by(subject_id=subject_id).count()
    if existing == 0:
        for i, name in enumerate(["信託法規", "信託契約", "信託實務"]):
            node = KnowledgeNode(
                subject_id=subject_id,
                name=name,
                depth=1 if i % 2 == 0 else 2,
                sort_order=i,
                source_origin="exam",
            )
            db.add(node)
            db.flush()
            context.ids[f"node_{name}"] = str(node.id)
        db.commit()


@given('管理員新匯入 {count:d} 題考古題到該考科')
def step_import_questions(context, count):
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}

    subject_id = uuid.UUID(context.memo["merge_subject_id"])

    # Create a dummy exam to hold the questions
    admin_id = None
    for key, val in context.ids.items():
        if "@" in key:
            admin_id = uuid.UUID(val)
            break
    assert admin_id, "找不到使用者帳號"

    exam = Exam(
        user_id=admin_id,
        subject_id=subject_id,
        total_questions=count,
        status="READY",
    )
    db.add(exam)
    db.flush()

    for i in range(count):
        q = Question(
            exam_id=exam.id,
            question_number=i + 1,
            content=f"考古題_{i+1}",
            correct_answer="A",
            source_type="historical",
        )
        db.add(q)
    db.flush()
    db.commit()

    # Store incoming_nodes for merge trigger (empty list, questions map internally)
    context.memo["imported_question_count"] = count
    context.memo["incoming_nodes"] = []


@given('考科 "{subject_name}" 已執行 {count:d} 次合併對齊')
def step_merge_history(context, subject_name, count):
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}

    subject_id_str = context.ids[f"subject_name_{subject_name}"]
    subject_id = uuid.UUID(subject_id_str)
    context.memo["merge_subject_id"] = subject_id_str

    # Create actual MergeHistory records in DB
    for i in range(count):
        sources = ["exam", "document", "document"]
        history = MergeHistory(
            subject_id=subject_id,
            trigger_source=sources[i % 3],
            trigger_name=f"merge_batch_{i+1}",
            nodes_added=3 + i,
            nodes_merged=2 + i,
            conflicts_count=i,
        )
        db.add(history)

    db.flush()
    db.commit()


@given('考科 "{subject_name}" 已經過多次合併對齊')
def step_multiple_merges(context, subject_name):
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}

    subject_id_str = context.ids[f"subject_name_{subject_name}"]
    subject_id = uuid.UUID(subject_id_str)
    context.memo["merge_subject_id"] = subject_id_str

    # Create nodes with parent relationships matching the expected Markdown tree
    # name, depth, parent_name, source
    node_defs = [
        ("信託法規", 1, None, "exam"),
        ("信託契約", 2, "信託法規", "document,exam"),
        ("信託財產獨立性", 3, "信託契約", "document"),
        ("受託人義務", 2, "信託法規", "document,exam"),
        ("忠實義務", 3, "受託人義務", "document"),
        ("信託實務", 1, None, "exam"),
        ("金錢信託", 2, "信託實務", "document,exam"),
        ("有價證券信託", 2, "信託實務", "document"),
        ("信託稅制", 1, None, "document"),
        ("信託課稅原則", 2, "信託稅制", "document"),
        ("贈與稅處理", 2, "信託稅制", "document"),
    ]
    node_ids = {}
    for i, (name, depth, parent_name, source) in enumerate(node_defs):
        if f"node_{name}" not in context.ids:
            parent_id = node_ids.get(parent_name) if parent_name else None
            node = KnowledgeNode(
                subject_id=subject_id,
                name=name,
                depth=depth,
                parent_id=parent_id,
                sort_order=i,
                source_origin=source,
            )
            db.add(node)
            db.flush()
            context.ids[f"node_{name}"] = str(node.id)
            node_ids[name] = node.id

    db.commit()


@given('節點 "{name}" 已合併考古題與教材來源')
def step_node_merged_sources(context, name):
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}

    subject_id_str = context.memo.get("merge_subject_id")
    if not subject_id_str:
        for key, val in context.ids.items():
            if key.startswith("subject_name_"):
                subject_id_str = val
                break
    subject_id = uuid.UUID(subject_id_str) if subject_id_str else None

    if f"node_{name}" not in context.ids:
        node = KnowledgeNode(
            subject_id=subject_id,
            name=name,
            depth=2,
            sort_order=0,
            source_origin="exam,document",
            exam_frequency="high",
            available_questions=10,
            source_text="教材原文段落引用",
        )
        db.add(node)
        db.flush()
        db.commit()
        context.ids[f"node_{name}"] = str(node.id)

    context.memo["query_node_name"] = name

    # Ensure merge history exists for last_merged_at
    if subject_id:
        existing_history = db.query(MergeHistory).filter_by(subject_id=subject_id).first()
        if not existing_history:
            history = MergeHistory(
                subject_id=subject_id,
                trigger_source="exam",
                trigger_name="initial_merge",
                nodes_added=1,
                nodes_merged=1,
                conflicts_count=0,
            )
            db.add(history)
            db.flush()
            db.commit()


@given('合併後新增了節點 "{name}"')
def step_new_node_after_merge(context, name):
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}

    subject_id_str = context.memo.get("merge_subject_id")
    if not subject_id_str:
        for key, val in context.ids.items():
            if key.startswith("subject_name_"):
                subject_id_str = val
                break
    subject_id = uuid.UUID(subject_id_str) if subject_id_str else None

    if f"node_{name}" not in context.ids:
        node = KnowledgeNode(
            subject_id=subject_id,
            name=name,
            depth=3,
            sort_order=0,
            source_origin="document",
        )
        db.add(node)
        db.flush()
        db.commit()
        context.ids[f"node_{name}"] = str(node.id)

    context.memo["new_merged_node"] = name
    context.memo["merge_subject_id"] = subject_id_str


@given('使用者 "{email}" 在節點 "{name}" 已有 mastery_rate: {rate:d}')
def step_user_mastery(context, email, name, rate):
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}

    user_id = uuid.UUID(context.ids[email])

    # Create node if it doesn't exist
    if f"node_{name}" not in context.ids:
        subject_id_str = context.memo.get("merge_subject_id")
        if not subject_id_str:
            for key, val in context.ids.items():
                if key.startswith("subject_name_"):
                    subject_id_str = val
                    break
        subject_id = uuid.UUID(subject_id_str) if subject_id_str else None
        node = KnowledgeNode(
            subject_id=subject_id,
            name=name,
            depth=2,
            sort_order=0,
            source_origin="exam",
        )
        db.add(node)
        db.flush()
        context.ids[f"node_{name}"] = str(node.id)
        context.memo["merge_subject_id"] = subject_id_str

    node_id = uuid.UUID(context.ids[f"node_{name}"])

    mastery = NodeMastery(
        user_id=user_id,
        node_id=node_id,
        mastery_rate=Decimal(str(rate)),
        correct_count=rate,
        total_count=100,
        color="orange" if rate < 80 else "green",
    )
    db.add(mastery)
    db.flush()
    db.commit()

    if not hasattr(context, "memo"):
        context.memo = {}
    context.memo[f"mastery_{name}_{email}"] = rate


@given('系統因新上傳觸發合併對齊')
def step_merge_triggered(context):
    if not hasattr(context, "memo"):
        context.memo = {}
    context.memo["merge_triggered"] = True
    # incoming_nodes should be empty since this is just a trigger
    context.memo.setdefault("incoming_nodes", [])
