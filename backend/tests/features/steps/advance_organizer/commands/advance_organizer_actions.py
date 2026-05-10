"""When steps — Feature 41 advance_organizer BDD."""

import uuid
from unittest.mock import patch

from behave import when

from app.models.resource import Resource


@when("_persist_parsed 處理 type=advance_organizer 鷹架")
def step_persist_parsed_advance_organizer(context):
    """Mock Gemini 回傳含 advance_organizer 的 parsed JSON，驗證 _persist_parsed 寫入 DB。"""
    from app.models.resource_parse_job import ParseJobStatus, ResourceParseJob
    from app.services.resource_parse_service import _persist_parsed

    db = context.db_session
    resource = db.get(Resource, uuid.UUID(context.memo["last_resource_id"]))
    assert resource is not None, "找不到測試資源"

    # 查已有 job，若無則建立
    job = db.query(ResourceParseJob).filter_by(resource_id=resource.id).first()
    if job is None:
        job = ResourceParseJob(
            resource_id=resource.id,
            tenant_id=resource.tenant_id,
            status=ParseJobStatus.SUCCESS.value,
            gemini_model="gemini-2.5-pro",
        )
        db.add(job)
        db.flush()

    # Mock parsed JSON，含 advance_organizer（≤ 80 字）
    parsed = {
        "markdown": "# 3.1 折現率\n\n折現率是反向利率計算。",
        "detected_content_type": "study_material",
        "critical_pages": [1],
        "questions": [],
        "scaffolds": [
            {
                "chapter_heading": "3.1 折現率",
                "type": "advance_organizer",
                "content": (
                    "💡 你可能已經知道：銀行存款 2% → 今天 100 元 = 明年 102 元。"
                    "折現率就是反過來：明年 102 元折回今天值多少。"
                    "這章學：不動產未來租金怎麼折回今天的價值。"
                ),
            },
            {
                "chapter_heading": "3.1 折現率",
                "type": "takeaway",
                "content": "• 折現率 = 風險報酬率 + 無風險利率",
            },
        ],
    }

    # patch embedding + node link（不打真實 API）
    with (
        patch("app.services.resource_parse_service._embed_scaffolds"),
        patch("app.services.resource_parse_service._link_scaffolds_to_nodes"),
        patch("app.services.resource_parse_service._generate_reference_answers"),
    ):
        result = _persist_parsed(db, resource, job, parsed)

    context.memo["persist_result"] = result


@when("查 information_schema enum_range(NULL::resource_scaffold_type)")
def step_query_enum_range(context):
    """查詢 DB enum 值清單。"""
    from sqlalchemy import text
    db = context.db_session
    row = db.execute(
        text("SELECT enum_range(NULL::resource_scaffold_type)")
    ).scalar()
    # psycopg3 回傳 list；psycopg2 / psycopg 回傳字串形如 {a,b,c}
    if isinstance(row, (list, tuple)):
        context.memo["enum_values"] = [str(v) for v in row]
    else:
        raw = str(row).strip("{}")
        context.memo["enum_values"] = [v.strip() for v in raw.split(",")]


_K06_TEMPLATE_IDS = [
    "K-06", "K-06-quiz", "K-06-video",
    "K-06-slides", "K-06-notes", "K-06-audio", "K-06-image",
]


@when("執行 seed_prompts")
def step_run_seed_prompts(context):
    """在 BDD DB 中 seed 最小限度的 K-06 系列模板（供 template 存在性驗證用）。

    因為 run_seed() 使用自己的 engine 無法注入 BDD session，
    此 step 直接在 BDD db_session 建立測試用模板 row。
    """
    from app.models.prompt_template import PromptTemplateV2
    db = context.db_session

    from app.models.prompt_template import PromptCategory

    name_map = {
        "K-06": "resource_parser_v2",
        "K-06-quiz": "resource_parser_quiz",
        "K-06-video": "resource_parser_video",
        "K-06-slides": "resource_parser_slides",
        "K-06-notes": "resource_parser_notes",
        "K-06-audio": "resource_parser_audio",
        "K-06-image": "resource_parser_image",
    }

    for tid in _K06_TEMPLATE_IDS:
        existing = db.query(PromptTemplateV2).filter_by(template_id=tid).first()
        if existing is None:
            tmpl = PromptTemplateV2(
                template_id=tid,
                name=name_map.get(tid, tid.lower().replace("-", "_")),
                display_name=f"{tid} 解析模板（BDD seed）",
                category=PromptCategory.KNOWLEDGE.value,
                model="gemini-2.5-pro",
                max_tokens=32768,
                temperature=0.1,
                system_prompt=f"# {tid} system prompt stub",
                user_prompt=f"# {tid} user prompt stub",
                variables=[],
                current_version=6 if tid == "K-06" else 1,
                is_active=True,
            )
            db.add(tmpl)
    db.commit()
    context.memo["seeded_template_ids"] = set(_K06_TEMPLATE_IDS)


@when("run_seed()")
def step_run_seed(context):
    """與「執行 seed_prompts」等價。"""
    step_run_seed_prompts(context)


@when("呼叫 _select_prompt_template(resource)")
def step_call_select_prompt_template(context):
    """呼叫路由函數並記錄結果。"""
    from app.services.resource_parse_service import _select_prompt_template

    r = context.memo.get("routing_resource")
    assert r is not None, "需要先執行 Given resource gcs_path=... step"
    result = _select_prompt_template(r)
    context.memo["selected_template"] = result
