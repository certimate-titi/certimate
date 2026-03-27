"""Then steps for Prompt template verification — ReadModel Then"""

from behave import then


@then('階段 {stage_id:d} Prompt 模板的版本號應遞增')
def step_impl(context, stage_id):
    response = context.last_response
    assert response.status_code in (200, 201), \
        f"預期成功，實際 {response.status_code}: {response.text}"

    data = response.json()
    version = data.get("version")
    assert version is not None, "回應中找不到版本號"
    assert version >= 2, f"版本號應遞增（至少為 2），但得到 {version}"


@then('後續生成的考題應使用新版 Prompt 模板')
def step_impl(context):
    # Verify the template was updated by checking DB
    db = context.db_session
    from app.models.prompt_template import PromptTemplate

    stage_id = context.memo.get("updated_stage_id", 3)
    template = db.query(PromptTemplate).filter_by(stage_order=stage_id).first()
    assert template is not None, f"找不到階段 {stage_id} 的 Prompt 模板"
    assert template.version >= 2, \
        f"模板版本應已遞增，但得到 {template.version}"


@then('回應應包含所有歷史版本：')
def step_impl(context):
    response = context.last_response
    assert response.status_code in (200, 201), \
        f"預期成功，實際 {response.status_code}: {response.text}"

    data = response.json()
    versions = data.get("versions", [])
    assert len(versions) >= len(context.table.rows), \
        f"應有至少 {len(context.table.rows)} 個歷史版本，但只有 {len(versions)}"

    for i, row in enumerate(context.table):
        expected_version = row["版本"]
        if i < len(versions):
            actual_version = versions[i].get("version", "")
            assert actual_version == expected_version, \
                f"第 {i+1} 個版本應為 '{expected_version}'，但得到 '{actual_version}'"
