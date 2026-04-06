"""Then Markdown 匯出包含來源標記 — ReadModel Then"""

from behave import then


@then('內容應包含來源標記，例如：')
def step_markdown_source_tags(context):
    response = context.last_response
    assert response.status_code == 200, \
        f"Markdown 匯出 API 失敗: {response.status_code}"

    # PlainTextResponse returns text, not JSON
    content = response.text
    expected_text = context.text.strip()

    # Verify key lines from the expected markdown are present
    expected_lines = [line.strip() for line in expected_text.split("\n") if line.strip()]
    for line in expected_lines:
        # Extract node name (between # and [)
        node_name = line.lstrip("#").strip().split("[")[0].strip()
        # Extract source tags
        source_tags = []
        for part in line.split("[")[1:]:
            tag = part.split("]")[0].strip()
            source_tags.append(tag)

        # Check node name appears in content
        assert node_name in content, \
            f"Markdown 缺少節點 '{node_name}'\n實際內容:\n{content}"

        # Check source tags appear near the node name
        for tag in source_tags:
            for t in tag.split(","):
                t = t.strip()
                assert f"[{t}]" in content, \
                    f"Markdown 缺少來源標記 '[{t}]'\n實際內容:\n{content}"
