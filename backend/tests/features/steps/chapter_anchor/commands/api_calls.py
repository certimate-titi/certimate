"""When 步驟 — K-RE-01 章節定錨 API 呼叫。"""

from behave import when, use_step_matcher


def _get_token(context, email: str) -> str:
    """取得指定 email 的 JWT token。"""
    user_id = context.ids[email]
    return context.jwt_helper.generate_token(user_id)


use_step_matcher("re")


@when(r'以 SUPER_ADMIN 呼叫 POST /api/v1/admin/scaffold-debug/generate-chapter-anchors/(?P<raw_sid>[^\s]+)')
def step_admin_generate_chapter_anchors(context, raw_sid):
    """以 SUPER_ADMIN 身分呼叫生成章節定錨 endpoint。

    raw_sid 可以是 {subject_id}（從 memo 取實際值）、UUID、或任意字串（測試非法輸入）。
    """
    from unittest.mock import patch

    token = _get_token(context, "admin@certimate.tw")

    # 若 raw_sid 是 placeholder，從 memo 取實際值
    if raw_sid == "{subject_id}":
        sid = context.memo.get("subject_id", "00000000-0000-0000-0000-000000000001")
    elif raw_sid == "{subject_b_id}":
        sid = context.memo.get("subject_b_id", "00000000-0000-0000-0000-000000000002")
    else:
        sid = raw_sid

    # Mock LLM 避免真實呼叫（BDD 環境無 API key）
    # 如果 sid 格式無效或科目不存在，mock 不會被呼叫（service 會先報錯）
    with patch(
        "app.services.chapter_anchor_service.ChapterAnchorService._call_llm",
        return_value="💡 想想：不同老師教法不同，AI 學習也是。這章學：監督/非監督/強化三大範式。",
    ):
        response = context.api_client.post(
            f"/api/v1/admin/scaffold-debug/generate-chapter-anchors/{sid}",
            headers={"Authorization": f"Bearer {token}"},
        )
    context.last_response = response


@when(r'以 SUPER_ADMIN 對科目 B 呼叫生成章節定錨端點')
def step_admin_generate_chapter_anchors_b(context):
    """以 SUPER_ADMIN 身分呼叫科目 B 的生成端點（跨科目隔離測試）。"""
    from unittest.mock import patch

    token = _get_token(context, "admin@certimate.tw")
    sid = context.memo.get("subject_b_id", "00000000-0000-0000-0000-000000000002")

    with patch(
        "app.services.chapter_anchor_service.ChapterAnchorService._call_llm",
        return_value="💡 想想：B科目日常情境。這章學：B科目核心方向。",
    ):
        response = context.api_client.post(
            f"/api/v1/admin/scaffold-debug/generate-chapter-anchors/{sid}",
            headers={"Authorization": f"Bearer {token}"},
        )
    context.last_response = response


@when(r'以 PRO 用戶呼叫 POST /api/v1/admin/scaffold-debug/generate-chapter-anchors/(?P<raw_sid>[^\s]+)')
def step_pro_user_generate_chapter_anchors(context, raw_sid):
    """以 PRO 用戶（非 SUPER_ADMIN）呼叫端點，預期 403。"""
    token = _get_token(context, "alice@example.com")
    sid = context.memo.get("subject_id", "00000000-0000-0000-0000-000000000001") \
        if raw_sid == "{subject_id}" else raw_sid
    response = context.api_client.post(
        f"/api/v1/admin/scaffold-debug/generate-chapter-anchors/{sid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when(r'以 PRO 用戶呼叫 GET /api/v1/knowledge-map/nodes/(?P<raw_nid>[^\s]+)/scaffolds')
def step_pro_user_get_node_scaffolds(context, raw_nid):
    """以 PRO 用戶取得葉節點 scaffold 列表。"""
    token = _get_token(context, "alice@example.com")
    nid = context.memo.get("leaf_node_id", "00000000-0000-0000-0000-000000000001") \
        if raw_nid == "{leaf_node_id}" else raw_nid
    response = context.api_client.get(
        f"/api/v1/knowledge-map/nodes/{nid}/scaffolds",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


use_step_matcher("parse")
