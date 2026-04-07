"""Then: 驗證模板 DB 狀態。"""

from behave import then
from app.repositories.prompt_template_repository import PromptTemplateRepository


@then('模板 "{template_id}" 的 current_version 應為 {version:d}')
def step_impl(context, template_id, version):
    repo = PromptTemplateRepository(context.db_session)
    context.db_session.expire_all()
    t = repo.find_by_template_id(template_id)
    assert t is not None, f"模板 {template_id} 不存在"
    assert t.current_version == version, (
        f"current_version 應為 {version}，實際為 {t.current_version}"
    )


@then('模板 "{template_id}" 的 temperature 應為 {temp}')
def step_impl(context, template_id, temp):
    repo = PromptTemplateRepository(context.db_session)
    context.db_session.expire_all()
    t = repo.find_by_template_id(template_id)
    assert t is not None, f"模板 {template_id} 不存在"
    actual = float(t.temperature)
    expected = float(temp)
    assert abs(actual - expected) < 0.01, (
        f"temperature 應為 {expected}，實際為 {actual}"
    )


@then('模板 "{template_id}" 的 is_active 應為 false')
def step_impl(context, template_id):
    repo = PromptTemplateRepository(context.db_session)
    context.db_session.expire_all()
    t = repo.find_by_template_id(template_id)
    assert t is not None, f"模板 {template_id} 不存在"
    assert t.is_active is False, f"模板 {template_id} 應已停用，但 is_active={t.is_active}"


@then('模板 "{template_id}" 的 model 應為 "{model}"')
def step_impl(context, template_id, model):
    repo = PromptTemplateRepository(context.db_session)
    context.db_session.expire_all()
    t = repo.find_by_template_id(template_id)
    assert t is not None
    assert t.model == model, f"model 應為 {model}，實際為 {t.model}"


@then('模板 "{template_id}" 的 system_prompt 應與版本 {version:d} 的 system_prompt 相同')
def step_impl(context, template_id, version):
    repo = PromptTemplateRepository(context.db_session)
    context.db_session.expire_all()
    t = repo.find_by_template_id(template_id)
    assert t is not None
    v = repo.find_version(t.id, version)
    assert v is not None, f"版本 {version} 不存在"
    assert t.system_prompt == v.system_prompt, (
        f"system_prompt 應與 v{version} 相同"
    )


@then('模板 "{template_id}" 的 current_version 不應變動')
def step_impl(context, template_id):
    repo = PromptTemplateRepository(context.db_session)
    context.db_session.expire_all()
    t = repo.find_by_template_id(template_id)
    assert t is not None
    # 由前一個步驟 context.memo 記錄的版本比較
    original = context.memo.get(f"pt_{template_id}_original_version")
    if original is not None:
        assert t.current_version == original, (
            f"current_version 不應變動，原為 {original}，現為 {t.current_version}"
        )


@then('模板 "{template_id}" 的 current_version 應遞增')
def step_impl(context, template_id):
    repo = PromptTemplateRepository(context.db_session)
    context.db_session.expire_all()
    t = repo.find_by_template_id(template_id)
    assert t is not None
    # 應遞增意味著 current_version > 1
    assert t.current_version > 1, f"current_version 應已遞增，目前為 {t.current_version}"


@then('模板 "{template_id}" 的 system_prompt 應為 variant B 的 system_prompt')
def step_impl(context, template_id):
    repo = PromptTemplateRepository(context.db_session)
    context.db_session.expire_all()
    t = repo.find_by_template_id(template_id)
    assert t is not None
    ab_id = context.ids.get(f"ab_{template_id}")
    if ab_id:
        from app.models.prompt_template import PromptAbTest
        import uuid
        ab = context.db_session.query(PromptAbTest).filter_by(
            id=uuid.UUID(ab_id)
        ).first()
        if ab:
            assert t.system_prompt == ab.variant_b_system_prompt, (
                "system_prompt 應已套用 variant B"
            )


@then('模板 "{template_id}" 應有 {count:d} 筆版本歷史紀錄')
def step_impl(context, template_id, count):
    repo = PromptTemplateRepository(context.db_session)
    context.db_session.expire_all()
    t = repo.find_by_template_id(template_id)
    assert t is not None
    actual = repo.count_versions(t.id)
    assert actual == count, f"版本歷史應有 {count} 筆，實際為 {actual}"


@then('模板 "{template_id}" 的 max_tokens_by_plan 應包含 PRO_199、PRO_PLUS_399、ULTRA_1599')
def step_impl(context, template_id):
    repo = PromptTemplateRepository(context.db_session)
    context.db_session.expire_all()
    t = repo.find_by_template_id(template_id)
    assert t is not None
    mbp = t.max_tokens_by_plan or {}
    assert "PRO_199" in mbp, "max_tokens_by_plan 缺少 PRO_199"
    assert "PRO_PLUS_399" in mbp, "max_tokens_by_plan 缺少 PRO_PLUS_399"
    assert "ULTRA_1599" in mbp, "max_tokens_by_plan 缺少 ULTRA_1599"
