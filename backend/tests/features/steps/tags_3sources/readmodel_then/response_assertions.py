"""Response assertions — Feature 54 Tags 3 Sources BDD."""

import io
import zipfile

from behave import then


@then('response JSON 中 items 含 tag normalized="{normalized}" count={count:d} sources breakdown {sources_json}')
def step_assert_aggregate_item_with_sources(context, normalized, count, sources_json):
    import json
    data = context.last_response.json()
    items = data.get("items", [])
    found = [i for i in items if i.get("normalized") == normalized]
    assert found, f"aggregate items 中找不到 normalized={normalized}，items={items}"
    item = found[0]
    actual_count = item.get("count", 0)
    assert actual_count == count, f"tag {normalized} count 應為 {count}，實際為 {actual_count}"
    expected_sources = json.loads(sources_json)
    actual_sources = item.get("sources", {})
    for k, v in expected_sources.items():
        assert actual_sources.get(k) == v, (
            f"tag {normalized} sources.{k} 應為 {v}，實際為 {actual_sources.get(k)}"
        )


@then('response JSON 中 items 含 tag normalized="{normalized}"')
def step_assert_aggregate_contains_tag(context, normalized):
    data = context.last_response.json()
    items = data.get("items", [])
    found = [i for i in items if i.get("normalized") == normalized]
    assert found, f"aggregate items 中找不到 normalized={normalized}，items={items}"


@then('response JSON 中 items 不含 tag normalized="{normalized}"')
def step_assert_aggregate_not_contains_tag(context, normalized):
    data = context.last_response.json()
    items = data.get("items", [])
    found = [i for i in items if i.get("normalized") == normalized]
    assert not found, f"aggregate items 不應含 normalized={normalized}，但找到了"


@then('response JSON 中 items 含 _kind "{kind}"')
def step_assert_items_contains_kind(context, kind):
    data = context.last_response.json()
    items = data.get("items", [])
    found = [i for i in items if i.get("_kind") == kind]
    assert found, f"items 中找不到 _kind={kind}，items={[i.get('_kind') for i in items]}"


@then('response JSON 中 total 為 {expected_total:d}')
def step_assert_items_total(context, expected_total):
    data = context.last_response.json()
    actual = data.get("total", -1)
    assert actual == expected_total, f"total 應為 {expected_total}，實際為 {actual}"


@then('ZIP 中含有前綴為 "{prefix}" 的 .md 檔案')
def step_assert_zip_contains_prefix(context, prefix):
    content = context.last_response.content
    buf = io.BytesIO(content)
    with zipfile.ZipFile(buf, "r") as zf:
        names = zf.namelist()
    found = [n for n in names if n.startswith(prefix)]
    assert found, f"ZIP 中找不到前綴為 '{prefix}' 的 .md 檔案，ZIP 內容: {names}"


@then('ZIP 中 index.md 含有 tag "#{tag_display}" 的 count breakdown（含 note: 和 annotation:）')
def step_assert_index_md_tag_breakdown(context, tag_display):
    content = context.last_response.content
    buf = io.BytesIO(content)
    with zipfile.ZipFile(buf, "r") as zf:
        assert "index.md" in zf.namelist(), "ZIP 中找不到 index.md"
        index_content = zf.read("index.md").decode("utf-8")

    assert tag_display in index_content, f"index.md 中找不到 tag #{tag_display}，內容:\n{index_content}"
    assert "note:" in index_content, f"index.md 中找不到 'note:' breakdown，內容:\n{index_content}"
    assert "annotation:" in index_content, f"index.md 中找不到 'annotation:' breakdown，內容:\n{index_content}"
