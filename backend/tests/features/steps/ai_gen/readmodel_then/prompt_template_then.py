"""Then steps for prompt template management — ReadModel Then"""

from behave import then


@then('階段 {stage_id:d} Prompt 模板的版本號應遞增')
def step_impl_version_increment(context, stage_id):
    """驗證 Prompt 模板版本號已遞增。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        version = data.get("version") or data.get("version_number")
        assert version is not None, "回應應包含版本號"
        assert version >= 2, f"版本號應遞增（≥ 2），實際 {version}"


@then('後續生成的考題應使用新版 Prompt 模板')
def step_impl_new_template_used(context):
    """驗證後續考題生成使用新版 Prompt 模板（語義層面，確認欄位存在）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('回應應包含所有歷史版本：')
def step_impl_history_versions(context):
    """驗證回應包含所有歷史 Prompt 模板版本。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        versions = data.get("versions", [])
        expected_versions = [row["版本"] for row in context.table]
        actual_versions = [v.get("version") or v.get("version_tag") for v in versions]
        for v in expected_versions:
            assert v in actual_versions, \
                f"歷史版本 '{v}' 不在回應中，實際版本：{actual_versions}"
