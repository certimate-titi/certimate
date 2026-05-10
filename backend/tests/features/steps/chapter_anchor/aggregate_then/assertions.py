"""Then 步驟 — K-RE-01 章節定錨 DB 斷言與 API 回應驗證。"""

import uuid

from behave import then

from app.models.knowledge_node import KnowledgeNode
from app.models.resource_scaffold import ResourceScaffold, ResourceScaffoldType
from app.models.scaffold_node_link import ScaffoldNodeLink


# ── HTTP 狀態碼 ──────────────────────────────────────────────────────────────

@then("HTTP {status_code:d}")
def step_http_status(context, status_code):
    """驗證 HTTP 狀態碼。"""
    actual = context.last_response.status_code
    assert actual == status_code, (
        f"HTTP 狀態碼不符。預期 {status_code}，實際 {actual}。"
        f"\n回應內容：{context.last_response.text[:300]}"
    )


# ── API 回應欄位驗證 ──────────────────────────────────────────────────────────

@then("回應含 chapters_processed >= 1")
def step_chapters_processed_gte_1(context):
    data = context.last_response.json()
    val = data.get("chapters_processed", 0)
    assert val >= 1, f"chapters_processed={val} 應 >= 1"


@then("回應含 scaffolds_created >= 1")
def step_scaffolds_created_gte_1(context):
    data = context.last_response.json()
    val = data.get("scaffolds_created", 0)
    assert val >= 1, f"scaffolds_created={val} 應 >= 1"


@then("回應含 skipped_already_exists >= 1")
def step_skipped_already_exists_gte_1(context):
    data = context.last_response.json()
    val = data.get("skipped_already_exists", 0)
    assert val >= 1, f"skipped_already_exists={val} 應 >= 1"


@then("回應含 scaffolds_created = 0")
def step_scaffolds_created_eq_0(context):
    data = context.last_response.json()
    val = data.get("scaffolds_created", -1)
    assert val == 0, f"scaffolds_created={val} 應 = 0"


@then("回應含 skipped_no_questions >= 1")
def step_skipped_no_questions_gte_1(context):
    data = context.last_response.json()
    val = data.get("skipped_no_questions", 0)
    assert val >= 1, f"skipped_no_questions={val} 應 >= 1"


@then('回應含 message "{expected_message}"')
def step_response_contains_message(context, expected_message):
    """驗證 response body 含指定 message 字串。"""
    resp = context.last_response
    try:
        body = resp.json()
    except Exception:
        body = {}

    # FastAPI HTTPException 的 detail 可能是 {"message": "..."} 或字串
    detail = body.get("detail", body)
    if isinstance(detail, dict):
        actual = detail.get("message", "")
    else:
        actual = str(detail)

    assert expected_message in actual, (
        f"回應 message 應含 '{expected_message}'，實際：{actual!r}"
    )


# ── DB 斷言 ───────────────────────────────────────────────────────────────────

@then("resource_scaffolds 新增 type='advance_organizer' template_code='K-RE-01'")
def step_db_advance_organizer_created(context):
    """驗證 DB 中已有 K-RE-01 advance_organizer scaffold。"""
    db = context.db_session
    # 重新 expire 讓 session 重新讀 DB
    db.expire_all()

    sid_str = context.memo.get("subject_id")
    if not sid_str:
        return

    sid = uuid.UUID(sid_str)

    rows = (
        db.query(ResourceScaffold)
        .join(ScaffoldNodeLink, ScaffoldNodeLink.scaffold_id == ResourceScaffold.id)
        .join(KnowledgeNode, KnowledgeNode.id == ScaffoldNodeLink.node_id)
        .filter(
            KnowledgeNode.subject_id == sid,
            ResourceScaffold.type == ResourceScaffoldType.ADVANCE_ORGANIZER.value,
            ResourceScaffold.template_code == "K-RE-01",
        )
        .all()
    )
    assert rows, (
        "resource_scaffolds 中找不到 type='advance_organizer' template_code='K-RE-01' "
        f"（subject_id={sid_str}）"
    )
    context.memo["created_scaffold"] = rows[0]


@then("scaffold 的 resource_id 為 NULL")
def step_scaffold_resource_id_null(context):
    """驗證 advance_organizer scaffold 的 resource_id 為 NULL。"""
    scaffold = context.memo.get("created_scaffold")
    if scaffold is None:
        # 重查
        db = context.db_session
        sid_str = context.memo.get("subject_id", "")
        if not sid_str:
            return
        sid = uuid.UUID(sid_str)
        scaffold = (
            db.query(ResourceScaffold)
            .join(ScaffoldNodeLink, ScaffoldNodeLink.scaffold_id == ResourceScaffold.id)
            .join(KnowledgeNode, KnowledgeNode.id == ScaffoldNodeLink.node_id)
            .filter(
                KnowledgeNode.subject_id == sid,
                ResourceScaffold.type == ResourceScaffoldType.ADVANCE_ORGANIZER.value,
                ResourceScaffold.template_code == "K-RE-01",
            )
            .first()
        )

    assert scaffold is not None, "找不到 advance_organizer scaffold 做驗證"
    assert scaffold.resource_id is None, (
        f"scaffold.resource_id 應為 NULL，實際為 {scaffold.resource_id}"
    )


@then("scaffold_node_links 新增連結到該章下所有 nodes（包含 depth=1 章節本身）")
def step_scaffold_links_include_chapter(context):
    """驗證 scaffold_node_links 包含章節本身。"""
    db = context.db_session
    chapter_id_str = context.memo.get("chapter_id")
    if not chapter_id_str:
        return

    chapter_id = uuid.UUID(chapter_id_str)
    scaffold = context.memo.get("created_scaffold")
    if scaffold is None:
        return

    link = (
        db.query(ScaffoldNodeLink)
        .filter(
            ScaffoldNodeLink.scaffold_id == scaffold.id,
            ScaffoldNodeLink.node_id == chapter_id,
        )
        .first()
    )
    assert link is not None, (
        f"scaffold_node_links 應包含章節 {chapter_id}，但找不到"
    )


@then("resource_scaffolds 不重複新增同章節 advance_organizer")
def step_no_duplicate_advance_organizer(context):
    """驗證冪等：同章節的 K-RE-01 advance_organizer 只有一個。"""
    db = context.db_session
    db.expire_all()

    chapter_id_str = context.memo.get("chapter_id")
    if not chapter_id_str:
        return
    chapter_id = uuid.UUID(chapter_id_str)

    rows = (
        db.query(ResourceScaffold)
        .join(ScaffoldNodeLink, ScaffoldNodeLink.scaffold_id == ResourceScaffold.id)
        .filter(
            ScaffoldNodeLink.node_id == chapter_id,
            ResourceScaffold.type == ResourceScaffoldType.ADVANCE_ORGANIZER.value,
            ResourceScaffold.template_code == "K-RE-01",
        )
        .all()
    )
    assert len(rows) == 1, (
        f"同章節 K-RE-01 advance_organizer 應只有 1 個，實際有 {len(rows)} 個"
    )


@then("該章節無 advance_organizer scaffold 被建立")
def step_no_scaffold_for_chapter_without_questions(context):
    """驗證無考古題的章節沒有 advance_organizer 被建立。"""
    db = context.db_session
    db.expire_all()

    sid_str = context.memo.get("subject_id", "")
    if not sid_str:
        return
    sid = uuid.UUID(sid_str)

    # 找「無題目章節」
    node = db.query(KnowledgeNode).filter_by(
        subject_id=sid, depth=1, name="無題目章節"
    ).first()
    if not node:
        return

    rows = (
        db.query(ResourceScaffold)
        .join(ScaffoldNodeLink, ScaffoldNodeLink.scaffold_id == ResourceScaffold.id)
        .filter(
            ScaffoldNodeLink.node_id == node.id,
            ResourceScaffold.type == ResourceScaffoldType.ADVANCE_ORGANIZER.value,
            ResourceScaffold.template_code == "K-RE-01",
        )
        .all()
    )
    assert not rows, (
        f"無考古題章節「無題目章節」不應有 advance_organizer，但找到 {len(rows)} 個"
    )


@then('科目 "AI規劃師" 的 advance_organizer scaffold 數量不變')
def step_subject_a_scaffold_count_unchanged(context):
    """驗證跨科目隔離：A 的 scaffold 數不因 B 觸發而改變。"""
    db = context.db_session
    db.expire_all()

    sid_str = context.memo.get("subject_id", "")
    if not sid_str:
        return
    sid = uuid.UUID(sid_str)

    before = context.memo.get("subject_a_scaffold_count_before", 0)
    after = (
        db.query(ResourceScaffold)
        .join(ScaffoldNodeLink, ScaffoldNodeLink.scaffold_id == ResourceScaffold.id)
        .join(KnowledgeNode, KnowledgeNode.id == ScaffoldNodeLink.node_id)
        .filter(
            KnowledgeNode.subject_id == sid,
            ResourceScaffold.type == ResourceScaffoldType.ADVANCE_ORGANIZER.value,
            ResourceScaffold.template_code == "K-RE-01",
        )
        .count()
    )
    assert after == before, (
        f"科目 A 的 K-RE-01 advance_organizer 數量不應改變：before={before}, after={after}"
    )


@then('科目 "B科目" 的 advance_organizer scaffold 新增')
def step_subject_b_scaffold_created(context):
    """驗證科目 B 有 advance_organizer scaffold 被建立。"""
    db = context.db_session
    db.expire_all()

    sid_str = context.memo.get("subject_b_id", "")
    if not sid_str:
        return
    sid = uuid.UUID(sid_str)

    rows = (
        db.query(ResourceScaffold)
        .join(ScaffoldNodeLink, ScaffoldNodeLink.scaffold_id == ResourceScaffold.id)
        .join(KnowledgeNode, KnowledgeNode.id == ScaffoldNodeLink.node_id)
        .filter(
            KnowledgeNode.subject_id == sid,
            ResourceScaffold.type == ResourceScaffoldType.ADVANCE_ORGANIZER.value,
            ResourceScaffold.template_code == "K-RE-01",
        )
        .all()
    )
    assert rows, f"科目 B 應有 K-RE-01 advance_organizer，但找不到（subject_id={sid_str}）"


# ── e2e 可見性斷言 ─────────────────────────────────────────────────────────────

@then("回應的 scaffolds 含至少 1 個 type='advance_organizer'")
def step_node_scaffolds_contains_advance_organizer(context):
    """驗證 GET /knowledge-map/nodes/{id}/scaffolds 回傳含 advance_organizer。"""
    resp = context.last_response
    assert resp.status_code == 200, (
        f"GET /knowledge-map/nodes/.../scaffolds 回傳 {resp.status_code}：{resp.text[:200]}"
    )
    data = resp.json()
    scaffolds = data.get("scaffolds", [])
    ao_list = [s for s in scaffolds if s.get("type") == "advance_organizer"]
    assert ao_list, (
        f"scaffolds 中應含 type='advance_organizer'，但只有：{[s.get('type') for s in scaffolds]}"
    )
    context.memo["e2e_ao_scaffold"] = ao_list[0]


@then("該 scaffold 的 template_code = 'K-RE-01'")
def step_ao_scaffold_template_code(context):
    """驗證 e2e 回應中的 advance_organizer scaffold 的 template_code 為 K-RE-01。"""
    scaffold = context.memo.get("e2e_ao_scaffold")
    if scaffold is None:
        return
    tc = scaffold.get("template_code", "")
    assert tc == "K-RE-01", (
        f"advance_organizer scaffold 的 template_code 應為 'K-RE-01'，實際為 {tc!r}"
    )
