"""Then DB-level cascade assertions for resource hard-delete + audit_log."""

from behave import then
from sqlalchemy import text


def _resolve_id(context, alias):
    return (
        context.ids.get(alias)
        or context.memo.get(f"deleted_resource_id_{alias}")
        or alias
    )


@then('資料庫中 resources 表的 {res_alias} row 不應存在')
def step_resource_gone(context, res_alias):
    rid = _resolve_id(context, res_alias)
    row = context.db_session.execute(
        text("SELECT id FROM resources WHERE id = :rid"), {"rid": rid}
    ).fetchone()
    assert row is None, f"resource {res_alias} ({rid}) 仍存在"


@then('資料庫中 resource_chunks 表不應存在任何 resource_id 為 {res_alias} 的 row')
def step_chunks_gone(context, res_alias):
    rid = _resolve_id(context, res_alias)
    row = context.db_session.execute(
        text("SELECT COUNT(*) FROM resource_chunks WHERE resource_id = :rid"),
        {"rid": rid},
    ).fetchone()
    assert row[0] == 0, f"仍有 {row[0]} 個 chunk 屬於 {res_alias}"
