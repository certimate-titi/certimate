"""Given 科目下有以下知識節點（含答對率與掌握顏色）— Aggregate Given"""

import uuid

from behave import given

from app.models.resource import Resource, ResourceStatus
from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery
from app.repositories.knowledge_node_repository import KnowledgeNodeRepository
from app.repositories.node_mastery_repository import NodeMasteryRepository
from app.repositories.resource_repository import ResourceRepository


@given('科目 "{subject}" 下有以下知識節點：')
def step_impl(context, subject):
    db = context.db_session
    node_repo = KnowledgeNodeRepository(db)
    mastery_repo = NodeMasteryRepository(db)
    resource_repo = ResourceRepository(db)

    if subject not in context.ids:
        raise KeyError(f"找不到科目 '{subject}' 的 ID")
    subject_id = uuid.UUID(context.ids[subject])

    # 追蹤已建立的來源資源（避免重複建立）
    resource_map = {}

    for row in context.table:
        node_id = uuid.UUID(int=int(row['節點 ID']))
        source_resource_name = row['來源資源']
        source_page = row['來源頁碼']
        source_ts = row['來源時間戳']
        mastery_rate = int(row['答對率'])
        color = row['掌握顏色']

        # 建立或取得來源資源
        if source_resource_name not in resource_map:
            # 找 Background 中哪個 user 備考此科目 — 用第一個有此科目 journey 的 user
            # 簡化：使用 context.memo 中的第一個 user
            user_id = None
            for key, val in context.ids.items():
                if '@' in key:
                    user_id = uuid.UUID(val)
                    break

            is_youtube = 'video' in source_resource_name.lower() or 'youtube' in source_resource_name.lower()
            resource = Resource(
                user_id=user_id,
                subject_id=subject_id,
                name=source_resource_name,
                type='youtube' if is_youtube else 'pdf',
                status=ResourceStatus.COMPLETED,
            )
            resource_repo.save(resource)
            resource_map[source_resource_name] = resource

        resource = resource_map[source_resource_name]

        # 建立知識節點
        node = KnowledgeNode(
            id=node_id,
            resource_id=resource.id,
            parent_id=None,
            name=row['名稱'],
            depth=1,
            sort_order=0,
            source_page_number=int(source_page) if source_page != 'null' else None,
            source_timestamp_seconds=int(source_ts) if source_ts != 'null' else None,
        )
        node_repo.save(node)

        # 儲存節點 ID 到 context
        context.ids[f"node_{row['節點 ID']}"] = str(node.id)

        # 建立掌握度記錄 — 為所有使用者建立
        for key, val in context.ids.items():
            if '@' in key:
                mastery = NodeMastery(
                    user_id=uuid.UUID(val),
                    node_id=node.id,
                    correct_count=mastery_rate,
                    total_count=100 if mastery_rate > 0 else 0,
                    mastery_rate=mastery_rate,
                    color=color,
                )
                mastery_repo.save(mastery)
