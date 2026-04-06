"""Then 衝突解決後的狀態驗證 — Aggregate Then"""

import uuid

from behave import then

from app.models.knowledge_node import KnowledgeNode
from app.models.merge_conflict import MergeConflict


@then('"{name}" 應成為 "{parent}" 的子節點')
def step_child_of_parent(context, name, parent):
    db = context.db_session
    db.expire_all()

    child_node = db.query(KnowledgeNode).filter_by(name=name).first()
    assert child_node, f"找不到節點 '{name}'"

    if child_node.parent_id:
        parent_node = db.query(KnowledgeNode).filter_by(id=child_node.parent_id).first()
        assert parent_node, f"找不到父節點 (id={child_node.parent_id})"
        assert parent_node.name == parent, \
            f"預期 '{name}' 的父節點為 '{parent}'，實際為 '{parent_node.name}'"
    else:
        assert False, f"節點 '{name}' 沒有父節點"


@then('該衝突狀態應更新為 "{status}"')
def step_conflict_status_updated(context, status):
    # Check from API response first
    response = context.last_response
    data = response.json()

    actual_status = data.get("status", "")
    assert actual_status == status, \
        f"預期衝突狀態為 '{status}'，實際為 '{actual_status}'"
