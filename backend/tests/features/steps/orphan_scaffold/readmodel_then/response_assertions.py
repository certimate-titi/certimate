"""Then — orphan scaffold API 回應斷言（readmodel_then）."""

from __future__ import annotations

from behave import then


@then('系統回應 {expected_code:d}')
def step_response_status_code(context, expected_code):
    resp = context.last_response
    assert resp.status_code == expected_code, (
        f"預期狀態碼 {expected_code}，實際 {resp.status_code}: {resp.text}"
    )


@then('系統以 AI_INFERRED trust_level 回傳鷹架')
def step_response_ai_inferred(context):
    resp = context.last_response
    assert resp.status_code == 200, f"預期 200，實際 {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body.get("trust_level") == "AI_INFERRED", (
        f"預期 trust_level=AI_INFERRED，實際 {body.get('trust_level')}"
    )


@then('鷹架包含 definition、illustration、practice_question 三段')
def step_response_has_three_sections(context):
    resp = context.last_response
    body = resp.json()
    content = body.get("content", {})
    assert "definition" in content, f"缺少 definition 欄位: {content}"
    assert "illustration" in content, f"缺少 illustration 欄位: {content}"
    assert "practice_question" in content, f"缺少 practice_question 欄位: {content}"
    pq = content["practice_question"]
    assert "stem" in pq, f"practice_question 缺 stem: {pq}"
    assert "options" in pq, f"practice_question 缺 options: {pq}"
    assert "answer" in pq, f"practice_question 缺 answer: {pq}"
    assert "explanation" in pq, f"practice_question 缺 explanation: {pq}"


@then('confidence_score 在 31 到 100 之間')
def step_confidence_in_range(context):
    resp = context.last_response
    body = resp.json()
    score = body.get("confidence_score")
    assert score is not None, "缺少 confidence_score 欄位"
    assert 31 <= score <= 100, f"confidence_score={score} 不在 31-100 範圍內"


@then('鷹架的 template_code 為 "{expected_code}"')
def step_template_code(context, expected_code):
    resp = context.last_response
    body = resp.json()
    actual = body.get("template_code")
    assert actual == expected_code, f"template_code 預期 {expected_code}，實際 {actual}"


@then('回應包含 fail_safe 欄位為 true')
def step_response_has_fail_safe(context):
    resp = context.last_response
    body = resp.json()
    detail = body.get("detail", body)
    assert detail.get("fail_safe") is True, (
        f"預期 fail_safe=true，實際 detail={detail}"
    )


@then('回應訊息包含 "{keyword}"')
def step_response_message_contains(context, keyword):
    resp = context.last_response
    body = resp.json()
    detail = body.get("detail", body)
    message = detail.get("message", "") if isinstance(detail, dict) else str(detail)
    assert keyword in message, f"回應訊息不含 '{keyword}'：{message}"


@then('信心分數為 {expected_score:d}')
def step_confidence_score_equals(context, expected_score):
    actual = context.memo.get("confidence_score")
    assert actual == expected_score, (
        f"信心分數預期 {expected_score}，實際 {actual}"
    )


@then('scaffold_review_queue 有 1 筆回報')
def step_review_queue_has_one(context):
    db = context.db_session
    from app.models.scaffold_review_queue import ScaffoldReviewQueue
    import uuid
    scaffold_id = uuid.UUID(context.ids["current_scaffold_id"])
    count = (
        db.query(ScaffoldReviewQueue)
        .filter(ScaffoldReviewQueue.scaffold_id == scaffold_id)
        .count()
    )
    assert count >= 1, f"scaffold_review_queue 預期 ≥1 筆，實際 {count}"


@then('鷹架的 trust_level 仍為 "{expected_trust_level}"（尚未達門檻）')
def step_trust_level_unchanged(context, expected_trust_level):
    db = context.db_session
    from app.models.resource_scaffold import ResourceScaffold
    import uuid
    scaffold_id = uuid.UUID(context.ids["current_scaffold_id"])
    scaffold = db.query(ResourceScaffold).filter(
        ResourceScaffold.id == scaffold_id
    ).first()
    db.refresh(scaffold)
    actual = scaffold.trust_level if scaffold else None
    assert actual == expected_trust_level, (
        f"trust_level 預期 {expected_trust_level}，實際 {actual}"
    )


@then('回應中 already_pending 為 true')
def step_already_pending_true(context):
    resp = context.last_response
    body = resp.json()
    assert body.get("already_pending") is True, (
        f"預期 already_pending=true，實際 {body}"
    )


@then('鷹架的 trust_level 變更為 "{expected_trust_level}"')
def step_trust_level_changed(context, expected_trust_level):
    db = context.db_session
    from app.models.resource_scaffold import ResourceScaffold
    import uuid
    scaffold_id = uuid.UUID(context.ids["current_scaffold_id"])
    scaffold = db.query(ResourceScaffold).filter(
        ResourceScaffold.id == scaffold_id
    ).first()
    db.refresh(scaffold)
    actual = scaffold.trust_level if scaffold else None
    assert actual == expected_trust_level, (
        f"trust_level 預期 {expected_trust_level}，實際 {actual}"
    )


@then('回應中 is_cached 為 true')
def step_is_cached_true(context):
    resp = context.last_response
    body = resp.json()
    assert body.get("is_cached") is True, (
        f"預期 is_cached=true，實際 {body}"
    )


@then('回應中 items 列表非空')
def step_items_not_empty(context):
    resp = context.last_response
    body = resp.json()
    items = body.get("items", [])
    assert len(items) > 0, f"預期 items 非空，實際 {body}"


@then('每筆 item 包含 scaffold_id、report_count、reason_codes')
def step_items_have_required_fields(context):
    resp = context.last_response
    body = resp.json()
    items = body.get("items", [])
    for item in items:
        assert "scaffold_id" in item, f"item 缺少 scaffold_id: {item}"
        assert "report_count" in item, f"item 缺少 report_count: {item}"
        assert "reason_codes" in item, f"item 缺少 reason_codes: {item}"
