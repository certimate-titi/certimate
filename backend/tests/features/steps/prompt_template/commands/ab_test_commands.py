"""When: A/B 測試操作。"""

from behave import when


def _parse_table_to_dict(table):
    data = {}
    for row in table:
        key = row["欄位"]
        val = row["值"]
        data[key] = val
    return data


@when('使用者 "{email}" 為模板 "{template_id}" 建立 A/B 測試：')
def step_impl(context, email, template_id):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    data = _parse_table_to_dict(context.table)

    if "traffic_split" in data:
        data["traffic_split"] = int(data["traffic_split"])
    if "variant_b_temperature" in data and data["variant_b_temperature"]:
        data["variant_b_temperature"] = float(data["variant_b_temperature"])

    response = context.api_client.post(
        f"/api/v1/admin/prompt-templates/{template_id}/ab-tests",
        json=data,
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response

    if response.status_code == 200:
        ab_id = response.json().get("ab_test_id")
        if ab_id:
            context.ids[f"ab_{template_id}"] = ab_id


@when('使用者 "{email}" 結束 A/B 測試 "{test_name}"，勝者為 "{winner}"')
def step_impl(context, email, test_name, winner):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    # 根據 test_name 找 test_id
    test_id = context.ids.get(test_name, test_name)

    response = context.api_client.patch(
        f"/api/v1/admin/prompt-templates/ab-tests/{test_id}",
        json={"action": "complete", "winner": winner},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 取消 A/B 測試 "{test_name}"')
def step_impl(context, email, test_name):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    test_id = context.ids.get(test_name, test_name)

    response = context.api_client.patch(
        f"/api/v1/admin/prompt-templates/ab-tests/{test_id}",
        json={"action": "cancel"},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when("AI 服務請求模板 \"{name}\"")
def step_impl(context, name):
    response = context.api_client.get(
        f"/api/v1/internal/prompt-templates/{name}",
    )
    context.last_response = response


@when("AI 服務為 user_id hash 值 {hash_val:d} 的用戶請求模板 \"{name}\"")
def step_impl(context, hash_val, name):
    response = context.api_client.get(
        f"/api/v1/internal/prompt-templates/{name}?user_id_hash={hash_val}",
    )
    context.last_response = response


@when("執行 Prompt 模板 seed 腳本")
def step_impl(context):
    """在測試環境中執行 seed 腳本，使用 Testcontainers DB。"""
    from app.scripts.seed_prompts import _scan_templates, _parse_md_file
    from app.models.prompt_template import PromptTemplateV2, PromptTemplateVersion
    from app.repositories.prompt_template_repository import PromptTemplateRepository

    repo = PromptTemplateRepository(context.db_session)
    file_templates = _scan_templates()

    # 若測試設定了 mock file version，覆蓋掃描結果
    for data in file_templates:
        tid = data["template_id"]
        memo_key = f"file_version_{tid}"
        if memo_key in context.memo:
            data["file_version"] = context.memo[memo_key]

    for data in file_templates:
        tid = data["template_id"]
        file_version = data["file_version"]

        existing = repo.find_by_template_id(tid)

        if not existing:
            template = PromptTemplateV2(
                template_id=tid,
                name=data["name"],
                display_name=data["display_name"],
                category=data["category"],
                model=data["model"],
                max_tokens=data["max_tokens"],
                max_tokens_by_plan=data.get("max_tokens_by_plan"),
                temperature=data["temperature"],
                system_prompt=data["system_prompt"],
                user_prompt=data["user_prompt"],
                variables=data.get("variables", []),
                feature_refs=data.get("feature_refs", []),
                current_version=file_version,
                is_active=True,
            )
            saved = repo.save(template)
            version_obj = PromptTemplateVersion(
                template_id=saved.id,
                version=file_version,
                model=saved.model,
                max_tokens=saved.max_tokens,
                max_tokens_by_plan=saved.max_tokens_by_plan,
                temperature=float(saved.temperature),
                system_prompt=saved.system_prompt,
                user_prompt=saved.user_prompt,
                variables=saved.variables or [],
                change_note="Seeded from file system (test)",
            )
            repo.save_version(version_obj)

        elif existing.current_version < file_version:
            old_version = existing.current_version
            existing.system_prompt = data["system_prompt"]
            existing.user_prompt = data["user_prompt"]
            existing.model = data["model"]
            existing.max_tokens = data["max_tokens"]
            existing.temperature = data["temperature"]
            existing.variables = data.get("variables", [])
            existing.current_version = file_version
            context.db_session.commit()
            version_obj = PromptTemplateVersion(
                template_id=existing.id,
                version=file_version,
                model=existing.model,
                max_tokens=existing.max_tokens,
                max_tokens_by_plan=existing.max_tokens_by_plan,
                temperature=float(existing.temperature),
                system_prompt=existing.system_prompt,
                user_prompt=existing.user_prompt,
                variables=existing.variables or [],
                change_note=f"Updated from file system v{old_version}→v{file_version} (test)",
            )
            repo.save_version(version_obj)

    context.memo["seed_executed"] = True
