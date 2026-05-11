"""Then assertions — Feature 38 pitfall BDD."""

import uuid

from behave import then

from app.models.resource_scaffold import ResourceScaffold


@then("resource_scaffolds 表新增一筆 type='{stype}'")
def step_assert_scaffold_type_present(context, stype):
    """驗證 DB 寫入指定 type 的 scaffold（取最近一筆對應 resource）。"""
    db = context.db_session
    rid = uuid.UUID(context.memo["last_resource_id"])
    rows = (
        db.query(ResourceScaffold)
        .filter_by(resource_id=rid, type=stype)
        .all()
    )
    assert rows, f"預期至少 1 筆 type='{stype}' 的 scaffold，實際 0 筆"
    context.memo["last_scaffold_row"] = rows[-1]


@then("該 row 的 retrieval_prompt 為 NULL")
def step_assert_retrieval_prompt_null(context):
    """驗證最近寫入的 scaffold row retrieval_prompt 欄為 NULL。"""
    row = context.memo.get("last_scaffold_row")
    assert row is not None, "需先執行 'resource_scaffolds 表新增一筆 type=...' step"
    val = getattr(row, "retrieval_prompt", None)
    assert val is None, f"預期 retrieval_prompt 為 NULL，實際={val!r}"


@then("該 row 的 template_code 為 '{code}'")
def step_assert_template_code(context, code):
    """驗證寫入的 scaffold template_code 欄。"""
    row = context.memo.get("last_scaffold_row")
    assert row is not None, "需先執行 'resource_scaffolds 表新增一筆 type=...' step"
    val = getattr(row, "template_code", None)
    assert val == code, f"預期 template_code={code!r}，實際={val!r}"


@then("resource_scaffolds 表只有 1 筆 (chapter='{chapter}', type='{stype}')")
def step_assert_scaffold_dedup_count(context, chapter, stype):
    """驗證同章節同 type 只保留 1 筆（dedup 效果）。"""
    db = context.db_session
    rid = uuid.UUID(context.memo["last_resource_id"])
    rows = (
        db.query(ResourceScaffold)
        .filter_by(resource_id=rid, type=stype, chapter_heading=chapter)
        .all()
    )
    assert len(rows) == 1, (
        f"預期 chapter={chapter!r} type={stype!r} 只 1 筆，實際 {len(rows)} 筆"
    )


def _collect_logs(context) -> str:
    """合併 memo 自家 handler 與 behave context.captured 兩處日誌。"""
    parts = list(context.memo.get("persist_logs") or [])
    parts += list(context.memo.get("parse_logs") or [])
    cap = getattr(context, "captured", None)
    if cap is not None:
        try:
            # behave 1.3 Captured 物件
            parts.append(str(getattr(cap, "log_output", "") or cap.make_report()))
        except Exception:
            try:
                parts.append(str(cap))
            except Exception:
                pass
    return "\n".join(parts)


@then('後端 log 含 "{snippet}"')
def step_assert_persist_log_contains(context, snippet):
    """驗證 _persist_parsed 期間 logger 輸出含指定片段。"""
    joined = _collect_logs(context)
    assert snippet in joined, (
        f"預期 log 含 {snippet!r}，實際:\n{joined or '(空)'}"
    )


@then('log 含 "{snippet}"')
def step_assert_any_log_contains(context, snippet):
    """log 含「片段」— 別名 step（無「後端」前綴）。"""
    step_assert_persist_log_contains(context, snippet)


@then("prompt_service 嘗試 '{template_name}' 失敗")
def step_assert_initial_template_load_failed(context, template_name):
    """驗證初始選用的 template 未在 DB 找到（觸發 fallback）。"""
    assert context.memo.get("initial_load_failed") is True, (
        f"預期 {template_name!r} 載入失敗，實際 initial_load_failed="
        f"{context.memo.get('initial_load_failed')!r}"
    )
    assert context.memo.get("initial_template_name") == template_name, (
        f"預期 initial_template_name={template_name!r}，"
        f"實際={context.memo.get('initial_template_name')!r}"
    )


@then("自動 fallback 載入 '{template_name}'")
def step_assert_fallback_to(context, template_name):
    """驗證 fallback 後實際載入 v2。"""
    assert context.memo.get("loaded_template_name") == template_name, (
        f"預期 fallback 至 {template_name!r}，實際 loaded="
        f"{context.memo.get('loaded_template_name')!r}"
    )
