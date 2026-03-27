"""Then 心智圖不應包含其他科目的節點 — ReadModel Then"""

from behave import then


@then('心智圖不應包含 {subject} 科目的節點')
def step_impl(context, subject):
    response = context.last_response
    data = response.json()

    nodes = data.get("nodes", [])
    for node in nodes:
        node_subject = node.get("subject_name", "")
        assert node_subject != subject, (
            f"回應中不應包含 '{subject}' 科目的節點，但發現: {node.get('name', '')}"
        )
