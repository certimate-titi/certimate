"""Then DB-level assertions for subject hard-delete cascade + audit log."""

import uuid

from behave import then
from sqlalchemy import text


def _resolve_id(context, alias):
    return context.ids.get(alias) or context.memo.get(f"deleted_subject_id_{alias}") or alias


@then('資料庫中科目 {subject_alias} 的 row 不應存在')
def step_subject_row_gone(context, subject_alias):
    sid = _resolve_id(context, subject_alias)
    row = context.db_session.execute(
        text("SELECT id FROM subjects WHERE id = :sid"), {"sid": sid}
    ).fetchone()
    assert row is None, f"科目 {subject_alias} ({sid}) 仍存在"


@then('資料庫中 knowledge_nodes 表不應存在 subject_id 為 {subject_alias} 的 row')
def step_knodes_gone(context, subject_alias):
    sid = _resolve_id(context, subject_alias)
    row = context.db_session.execute(
        text("SELECT COUNT(*) FROM knowledge_nodes WHERE subject_id = :sid"),
        {"sid": sid},
    ).fetchone()
    assert row[0] == 0, f"仍有 {row[0]} 個 knowledge_node 屬於 {subject_alias}"


@then('資料庫中 exams 表不應存在 subject_id 為 {subject_alias} 的 row')
def step_exams_gone(context, subject_alias):
    sid = _resolve_id(context, subject_alias)
    row = context.db_session.execute(
        text("SELECT COUNT(*) FROM exams WHERE subject_id = :sid"),
        {"sid": sid},
    ).fetchone()
    assert row[0] == 0, f"仍有 {row[0]} 個 exam 屬於 {subject_alias}"


@then('資料庫中 admin_audit_logs 應有一筆 action 為 "{action}" 且 target_id 為 {target_alias} 的紀錄')
def step_audit_log_exists(context, action, target_alias):
    tid = _resolve_id(context, target_alias)
    row = context.db_session.execute(
        text(
            "SELECT COUNT(*) FROM admin_audit_logs "
            "WHERE action = :action AND target_id = :tid"
        ),
        {"action": action, "tid": tid},
    ).fetchone()
    assert row[0] >= 1, (
        f"找不到 action={action}, target_id={tid} 的 audit log"
    )
