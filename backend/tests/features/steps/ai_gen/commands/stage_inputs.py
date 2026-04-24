"""When 階段 Prompt 輸入 — Command"""

from behave import when

from app.services.ai_generation_service import AiGenerationService


@when('階段 1 Prompt 以節點 1 (EC2) 和節點 2 (S3) 的向量化內容為輸入')
def step_stage1_input(context):
    db = context.db_session
    service = AiGenerationService(db)

    from app.models.knowledge_node import KnowledgeNode
    import uuid

    nodes = []
    for nid in [1, 2]:
        key = f"node_{nid}"
        if key in context.ids:
            node = db.query(KnowledgeNode).filter_by(
                id=uuid.UUID(context.ids[key])
            ).first()
            if node:
                nodes.append(node)

    bloom_source = context.memo.get("bloom_source")
    bloom_dist = context.memo.get("bloom_distribution")
    if bloom_source:
        service._bloom_override = {"source": bloom_source, "distribution": bloom_dist}

    difficulty_dist = {"easy": 30, "medium": 50, "hard": 20}
    result = service._stage1_exam_point_analysis(nodes, 10, difficulty_dist)
    context.memo["stage_1_output"] = result
    context.memo["stage_1_completed"] = True
    context.memo["exam_question_count"] = 10


@when('階段 2 Prompt 以階段 1 輸出與難易度分配為輸入')
def step_stage2_input(context):
    db = context.db_session
    service = AiGenerationService(db)

    stage1 = context.memo.get("stage_1_output")
    assert stage1 is not None, "階段 1 尚未完成"

    difficulty_dist = {"easy": 30, "medium": 50, "hard": 20}
    total_q = context.memo.get("total_questions", 10)

    result = service._stage2_question_generation(stage1, difficulty_dist, None, total_q)
    context.memo["stage_2_output"] = result


@when('階段 3 Prompt 以階段 2 輸出為輸入')
def step_stage3_input(context):
    db = context.db_session
    service = AiGenerationService(db)

    stage2 = context.memo.get("stage_2_output")
    assert stage2 is not None, "階段 2 尚未完成"

    result = service._stage3_distractor_optimization(stage2, None)
    context.memo["stage_3_output"] = result


@when('階段 4 Prompt 以階段 3 輸出為輸入')
def step_stage4_input(context):
    db = context.db_session
    service = AiGenerationService(db)

    stage3 = context.memo.get("stage_3_output")
    assert stage3 is not None, "階段 3 尚未完成"

    exam_id = context.memo.get("current_exam_id", "test-exam-id")
    result = service._stage4_formatted_output(stage3, exam_id)
    context.memo["stage_4_output"] = result
