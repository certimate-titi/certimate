"""When steps for individual stage Prompt inputs — Command"""

import uuid

from behave import when

from app.services.ai_generation_service import AiGenerationService


@when('階段 1 Prompt 以節點 {node1_id:d} ({node1_name}) 和節點 {node2_id:d} ({node2_name}) 的向量化內容為輸入')
def step_impl(context, node1_id, node1_name, node2_id, node2_name):
    db = context.db_session
    service = AiGenerationService(db)

    from app.models.knowledge_node import KnowledgeNode

    node_ids_uuids = []
    for nid in [node1_id, node2_id]:
        key = f"node_{nid}"
        if key in context.ids:
            node_ids_uuids.append(uuid.UUID(context.ids[key]))
        else:
            node_ids_uuids.append(uuid.UUID(int=nid))

    nodes = db.query(KnowledgeNode).filter(
        KnowledgeNode.id.in_(node_ids_uuids)
    ).all()

    difficulty_dist = context.memo.get("difficulty_distribution", {"easy": 30, "medium": 50, "hard": 20})
    total_q = context.memo.get("total_questions", 10)

    bloom_source = context.memo.get("bloom_source")
    bloom_dist = context.memo.get("bloom_distribution")
    if bloom_source:
        service._bloom_override = {"source": bloom_source, "distribution": bloom_dist}

    result = service._stage1_exam_point_analysis(nodes, total_q, difficulty_dist)
    context.memo["stage1_result"] = result
    context.memo["exam_question_count"] = total_q


@when('階段 2 Prompt 以階段 1 輸出與難易度分配為輸入')
def step_impl(context):
    db = context.db_session
    service = AiGenerationService(db)

    stage1 = context.memo.get("stage1_result")
    if not stage1:
        raise KeyError("找不到階段 1 的輸出結果")

    difficulty_dist = context.memo.get("difficulty_distribution", {"easy": 30, "medium": 50, "hard": 20})
    total_q = context.memo.get("total_questions", 10)
    user_context = context.memo.get("user_context")

    result = service._stage2_question_generation(stage1, difficulty_dist, user_context, total_q)
    context.memo["stage2_result"] = result


@when('階段 3 Prompt 以階段 2 輸出為輸入')
def step_impl(context):
    db = context.db_session
    service = AiGenerationService(db)

    stage2 = context.memo.get("stage2_result")
    if not stage2:
        raise KeyError("找不到階段 2 的輸出結果")

    user_context = context.memo.get("user_context")
    result = service._stage3_distractor_optimization(stage2, user_context)
    context.memo["stage3_result"] = result


@when('階段 4 Prompt 以階段 3 輸出為輸入')
def step_impl(context):
    db = context.db_session
    service = AiGenerationService(db)

    stage3 = context.memo.get("stage3_result")
    if not stage3:
        raise KeyError("找不到階段 3 的輸出結果")

    exam_id = context.memo.get("current_exam_id", str(uuid.uuid4()))
    result = service._stage4_formatted_output(stage3, exam_id)
    context.memo["stage4_result"] = result
