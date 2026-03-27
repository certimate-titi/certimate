"""Given 使用者在科目的答題統計 — Aggregate Given"""

import uuid
from datetime import date
from decimal import Decimal

from behave import given

from app.models.subject import SubjectCategory, Subject
from app.models.knowledge_node import KnowledgeNode
from app.models.question_stat import QuestionStat
from app.models.resource import Resource, ResourceType, ResourceStatus, ResourceScope


@given('使用者 "{email}" 在 {subject_name} 科目的答題統計如下：')
def step_impl(context, email, subject_name):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])

    subj_key = f"subject_{subject_name}"
    subject_id = uuid.UUID(context.ids[subj_key])

    # Create resource if needed
    if "default_resource" not in context.ids:
        res = Resource(
            user_id=user_uuid,
            subject_id=subject_id,
            name="test.pdf",
            type=ResourceType.PDF,
            status=ResourceStatus.COMPLETED,
            scope=ResourceScope.PERSONAL,
        )
        db.add(res)
        db.flush()
        context.ids["default_resource"] = str(res.id)

    resource_id = uuid.UUID(context.ids["default_resource"])

    for row in context.table:
        node_name = row["知識節點"]
        success = int(row["成功次數"])
        fail = int(row["失敗次數"])
        ef = Decimal(row["Ease Factor"])
        review_str = row["下次複習日"]

        # Create node
        node_key = f"node_{node_name}"
        if node_key not in context.ids:
            node = KnowledgeNode(
                resource_id=resource_id,
                name=node_name,
                depth=1,
                sort_order=0,
            )
            db.add(node)
            db.flush()
            context.ids[node_key] = str(node.id)

        node_id = uuid.UUID(context.ids[node_key])
        review_date = date.fromisoformat(review_str) if review_str and review_str != "null" else None

        stat = QuestionStat(
            user_id=user_uuid,
            node_id=node_id,
            success_count=success,
            fail_count=fail,
            ease_factor=ef,
            next_review_date=review_date,
        )
        db.add(stat)

    db.commit()
