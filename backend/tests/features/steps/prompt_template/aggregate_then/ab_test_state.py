"""Then: 驗證 A/B 測試 DB 狀態。"""

import uuid
from behave import then

from app.models.prompt_template import PromptAbTest
from app.repositories.prompt_template_repository import PromptTemplateRepository


def _find_ab(context, test_id_or_name: str):
    # 先嘗試從 context.ids 找 UUID
    raw_id = context.ids.get(test_id_or_name, test_id_or_name)
    try:
        uid = uuid.UUID(raw_id)
        ab = context.db_session.query(PromptAbTest).filter_by(id=uid).first()
        if ab:
            context.db_session.refresh(ab)
            return ab
    except (ValueError, AttributeError):
        pass
    # Fallback: 用名稱查詢
    return (
        context.db_session.query(PromptAbTest)
        .filter_by(name=test_id_or_name)
        .first()
    )


@then('A/B 測試 "{test_id}" 的 status 應為 "{status}"')
def step_impl(context, test_id, status):
    ab = _find_ab(context, test_id)
    assert ab is not None, f"A/B 測試 {test_id} 不存在"
    assert ab.status == status, f"status 應為 {status}，實際為 {ab.status}"


@then('A/B 測試 "{test_id}" 的 winner 應為 "{winner}"')
def step_impl(context, test_id, winner):
    ab = _find_ab(context, test_id)
    assert ab is not None, f"A/B 測試 {test_id} 不存在"
    assert ab.winner == winner, f"winner 應為 {winner}，實際為 {ab.winner}"


@then("A/B 測試的 variant_a_version 應為模板 \"{template_id}\" 的 current_version")
def step_impl(context, template_id):
    repo = PromptTemplateRepository(context.db_session)
    t = repo.find_by_template_id(template_id)
    assert t is not None

    # 找最新建立的 ab test
    ab_id = context.ids.get(f"ab_{template_id}")
    if ab_id:
        ab = context.db_session.query(PromptAbTest).filter_by(
            id=uuid.UUID(ab_id)
        ).first()
    else:
        ab = (
            context.db_session.query(PromptAbTest)
            .filter_by(template_id=t.id)
            .order_by(PromptAbTest.created_at.desc())
            .first()
        )

    assert ab is not None, "A/B 測試不存在"
    assert ab.variant_a_version == t.current_version, (
        f"variant_a_version 應為 {t.current_version}，實際為 {ab.variant_a_version}"
    )


@then("A/B 測試的 status 應為 \"{status}\"")
def step_impl(context, status):
    # 從 last_response 取得 ab_test_id
    data = context.last_response.json()
    ab_id = data.get("ab_test_id")
    assert ab_id is not None

    ab = context.db_session.query(PromptAbTest).filter_by(
        id=uuid.UUID(ab_id)
    ).first()
    assert ab is not None
    assert ab.status == status, f"status 應為 {status}，實際為 {ab.status}"
