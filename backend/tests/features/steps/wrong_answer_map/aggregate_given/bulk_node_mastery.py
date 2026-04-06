"""Given 使用者的各節點掌握度 — Aggregate Given"""

import uuid
from decimal import Decimal

from behave import given

from app.models.node_mastery import NodeMastery


@given('使用者 "{email}" 的各節點掌握度如下：')
def step_impl(context, email):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    for row in context.table:
        node_name = row["節點名稱"]
        rate_str = row["答對率"].replace("%", "").strip()
        rate = int(rate_str)

        node_id = uuid.UUID(context.ids[f"node_{node_name}"])

        # Compute color
        if rate == 0:
            color = "gray"
        elif rate < 60:
            color = "red"
        elif rate < 80:
            color = "orange"
        else:
            color = "green"

        # Simulate counts
        total_count = 10
        correct_count = round(rate * total_count / 100)

        mastery = NodeMastery(
            user_id=user_id,
            node_id=node_id,
            correct_count=correct_count,
            total_count=total_count if rate > 0 else 0,
            mastery_rate=Decimal(str(rate)),
            color=color,
        )
        db.add(mastery)

    db.commit()


@given('使用者 "{email}" 的子節點掌握度如下：')
def step_impl_child(context, email):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    for row in context.table:
        node_name = row["節點名稱"]
        rate = int(row["mastery_rate"])

        node_id = uuid.UUID(context.ids[f"node_{node_name}"])

        if rate < 60:
            color = "red"
        elif rate < 80:
            color = "orange"
        else:
            color = "green"

        total_count = 10
        correct_count = round(rate * total_count / 100)

        mastery = NodeMastery(
            user_id=user_id,
            node_id=node_id,
            correct_count=correct_count,
            total_count=total_count,
            mastery_rate=Decimal(str(rate)),
            color=color,
        )
        db.add(mastery)

    db.commit()
