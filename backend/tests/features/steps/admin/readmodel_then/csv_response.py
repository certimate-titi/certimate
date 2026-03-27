"""Then 回應應為 CSV 檔案，包含指定欄位 — Read Model Then"""

from behave import then


@then('回應應為 CSV 檔案，包含欄位：{fields_str}')
def step_impl(context, fields_str):
    response = context.last_response
    content_type = response.headers.get("content-type", "")
    assert "text/csv" in content_type, \
        f"預期 text/csv，實際 content-type: {content_type}"

    content = response.text
    first_line = content.split("\n")[0].strip()
    expected_fields = [f.strip() for f in fields_str.split("、")]

    for field in expected_fields:
        assert field in first_line, \
            f"CSV 標頭中缺少欄位 '{field}'，實際標頭: {first_line}"
