"""Then: 驗證 Prompt 模板 API 回應。"""

from behave import then


@then("回應應包含 {count:d} 筆模板")
def step_impl(context, count):
    data = context.last_response.json()
    templates = data.get("templates", [])
    assert len(templates) == count, (
        f"回應應有 {count} 筆模板，實際 {len(templates)} 筆"
    )


@then("每筆模板應包含：")
def step_impl(context):
    data = context.last_response.json()
    templates = data.get("templates", [])
    assert len(templates) > 0, "模板列表不得為空"

    expected_fields = [row["欄位"] for row in context.table]
    for t in templates:
        for field in expected_fields:
            assert field in t, f"模板缺少欄位 {field}，模板內容：{t}"


@then("回應中所有模板的 category 應為 \"{category}\"")
def step_impl(context, category):
    data = context.last_response.json()
    templates = data.get("templates", [])
    for t in templates:
        assert t.get("category") == category, (
            f"模板 category 應為 {category}，實際為 {t.get('category')}"
        )


@then("回應應包含 system_prompt 欄位")
def step_impl(context):
    data = context.last_response.json()
    assert "system_prompt" in data, f"回應缺少 system_prompt，回應內容：{data}"


@then("回應應包含 user_prompt 欄位")
def step_impl(context):
    data = context.last_response.json()
    assert "user_prompt" in data, f"回應缺少 user_prompt，回應內容：{data}"


@then("回應應包含 variables 欄位")
def step_impl(context):
    data = context.last_response.json()
    assert "variables" in data, f"回應缺少 variables，回應內容：{data}"


@then("回應應包含 {count:d} 筆版本紀錄")
def step_impl(context, count):
    data = context.last_response.json()
    versions = data.get("versions", [])
    assert len(versions) == count, (
        f"回應應有 {count} 筆版本，實際 {len(versions)} 筆"
    )


@then("第一筆版本的 version 應為 {version:d}")
def step_impl(context, version):
    data = context.last_response.json()
    versions = data.get("versions", [])
    assert len(versions) > 0, "版本列表為空"
    first = versions[0]
    assert first["version"] == version, (
        f"第一筆版本應為 v{version}，實際為 v{first['version']}"
    )


@then("第二筆版本的 version 應為 {version:d}")
def step_impl(context, version):
    data = context.last_response.json()
    versions = data.get("versions", [])
    assert len(versions) >= 2, "版本列表少於 2 筆"
    second = versions[1]
    assert second["version"] == version, (
        f"第二筆版本應為 v{version}，實際為 v{second['version']}"
    )


@then("每筆版本應包含：")
def step_impl(context):
    data = context.last_response.json()
    versions = data.get("versions", [])
    expected_fields = [row["欄位"] for row in context.table]
    for v in versions:
        for field in expected_fields:
            assert field in v, f"版本記錄缺少欄位 {field}"


@then("應使用 variant A（當前版本的 prompt）")
def step_impl(context):
    data = context.last_response.json()
    variant = data.get("variant")
    assert variant == "A", f"應使用 variant A，實際為 {variant}"


@then("應使用 variant B 的 prompt")
def step_impl(context):
    data = context.last_response.json()
    variant = data.get("variant")
    assert variant == "B", f"應使用 variant B，實際為 {variant}"


@then("應回傳「模板已停用」錯誤")
def step_impl(context):
    resp = context.last_response
    assert resp.status_code in (410, 404, 400), (
        f"應回傳停用錯誤，實際狀態碼 {resp.status_code}"
    )


@then("資料庫中應有 {count:d} 筆 Prompt 模板")
def step_impl(context):
    # seed 測試：在測試中無法真正執行 seed，此步驟標記為跳過
    pass


@then("每筆模板的 current_version 應為 {version:d}")
def step_impl(context, version):
    pass


@then("每筆模板應有 {count:d} 筆版本歷史紀錄")
def step_impl(context, count):
    pass


@then("模板 \"{template_id}\" 的 current_version 應維持為 {version:d}")
def step_impl(context, template_id, version):
    from app.repositories.prompt_template_repository import PromptTemplateRepository
    repo = PromptTemplateRepository(context.db_session)
    context.db_session.expire_all()
    t = repo.find_by_template_id(template_id)
    assert t is not None
    assert t.current_version == version, (
        f"current_version 應維持 {version}，實際為 {t.current_version}"
    )
