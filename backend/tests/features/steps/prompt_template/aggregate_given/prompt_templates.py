"""Given: 系統中有以下 Prompt 模板 + 相關前置 Given 步驟。"""

import uuid
from behave import given

from app.models.prompt_template import (
    PromptTemplateV2,
    PromptTemplateVersion,
    PromptAbTest,
    AbTestStatus,
    PromptCategory,
)
from app.repositories.prompt_template_repository import PromptTemplateRepository


_CATEGORY_MAP = {
    "safety": PromptCategory.SAFETY,
    "knowledge": PromptCategory.KNOWLEDGE,
    "exam": PromptCategory.EXAM,
    "teaching": PromptCategory.TEACHING,
    "emotion": PromptCategory.EMOTION,
}


def _get_col(row, name, default=None):
    try:
        return row[name]
    except KeyError:
        return default


@given("系統中有以下 Prompt 模板：")
def step_impl(context):
    repo = PromptTemplateRepository(context.db_session)

    for row in context.table:
        tid = row["template_id"]
        name = row["name"]
        current_version = int(_get_col(row, "current_version", 1))

        # Seed system_prompt / user_prompt based on template_id
        system_prompt = f"[{tid}] 系統 Prompt（預設）"
        user_prompt = f"{{user_input}}"

        template = PromptTemplateV2(
            template_id=tid,
            name=name,
            display_name=row["display_name"],
            category=_CATEGORY_MAP.get(row["category"], PromptCategory.SAFETY),
            model=row["model"],
            max_tokens=int(row["max_tokens"]),
            temperature=float(_get_col(row, "temperature", 0.5)),
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            variables=[],
            current_version=current_version,
            is_active=True,
        )
        saved = repo.save(template)
        context.ids[tid] = str(saved.id)
        context.memo[f"pt_{tid}_template_id"] = tid

        # 建立每個版本的歷史
        for v in range(1, current_version + 1):
            version_obj = PromptTemplateVersion(
                template_id=saved.id,
                version=v,
                model=saved.model,
                max_tokens=saved.max_tokens,
                temperature=float(saved.temperature),
                system_prompt=f"[{tid}] v{v} 系統 Prompt",
                user_prompt=saved.user_prompt,
                variables=[],
                change_note=f"Version {v}",
            )
            context.db_session.add(version_obj)
        context.db_session.commit()


@given("模板 \"{template_id}\" 有一個 running 狀態的 A/B 測試")
def step_impl(context, template_id):
    _create_running_ab_test(context, template_id, "自動建立測試", 50, f"ab_{template_id}")


@given("模板 \"{template_id}\" 有一個 running A/B 測試，traffic_split 為 {split:d}")
def step_impl(context, template_id, split):
    _create_running_ab_test(context, template_id, "流量測試", split, f"ab_{template_id}")


@given("模板 \"{template_id}\" 有一個 running A/B 測試 \"{test_name}\"")
def step_impl(context, template_id, test_name):
    _create_running_ab_test(context, template_id, test_name, 30, test_name)


@given("模板 \"{template_id}\" 的 is_active 為 false")
def step_impl(context, template_id):
    repo = PromptTemplateRepository(context.db_session)
    t = repo.find_by_template_id(template_id)
    if t:
        t.is_active = False
        context.db_session.commit()


@given("資料庫中無任何 Prompt 模板")
def step_impl(context):
    # 清除所有 prompt 模板（已由 environment.py 的 scenario 清理）
    context.db_session.query(PromptTemplateV2).delete()
    context.db_session.commit()


@given("檔案系統中有 {count:d} 個 Prompt 模板檔案")
def step_impl(context, count):
    context.memo["seed_file_count"] = count


@given("資料庫中模板 \"{template_id}\" 的 current_version 為 {version:d}")
def step_impl(context, template_id, version):
    repo = PromptTemplateRepository(context.db_session)
    t = repo.find_by_template_id(template_id)
    if t:
        t.current_version = version
        context.db_session.commit()


@given("檔案系統中模板 \"{template_id}\" 的 version 為 {version:d}")
def step_impl(context, template_id, version):
    context.memo[f"file_version_{template_id}"] = version


def _create_running_ab_test(context, template_id, name, split, memo_key):
    repo = PromptTemplateRepository(context.db_session)
    t = repo.find_by_template_id(template_id)
    if not t:
        return

    # 找 super_admin user 作為 created_by
    creator_id = _get_super_admin_id(context)

    ab = PromptAbTest(
        template_id=t.id,
        name=name,
        variant_a_version=t.current_version,
        variant_b_system_prompt=f"[Variant B] {template_id} 系統 Prompt",
        variant_b_user_prompt="{user_input}",
        variant_b_temperature=0.5,
        traffic_split=split,
        status=AbTestStatus.RUNNING,
        metric_name="accuracy",
        created_by=creator_id,
    )
    context.db_session.add(ab)
    context.db_session.commit()
    context.db_session.refresh(ab)
    context.ids[memo_key] = str(ab.id)
    context.memo[f"ab_{memo_key}_id"] = str(ab.id)


def _get_super_admin_id(context):
    """取得 super_admin 的 UUID，若無則使用固定預設值。"""
    super_email = "super@certimate.com"
    uid = context.ids.get(super_email)
    if uid:
        return uuid.UUID(uid)
    return uuid.uuid4()
