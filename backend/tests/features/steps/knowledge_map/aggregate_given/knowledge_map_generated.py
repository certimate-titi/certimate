from behave import given
from app.models.resource import Resource, ResourceType, ResourceStatus
from app.models.knowledge_node import KnowledgeNode
from app.models.subject import Subject
from app.models.learning_journey import LearningJourney


@given('系統已完成 "{filename}" 的心智圖生成')
def step_impl(context, filename):
    db = context.db_session

    # 使用 Background 中建立的第一個使用者
    user_id = context.ids.get("pro@example.com") or context.ids.get("1")
    assert user_id is not None, "找不到可用的使用者 ID"

    subject = db.query(Subject).first()
    assert subject is not None, "系統中尚無學科，請先建立學科庫"

    # 確保有學習歷程
    journey = db.query(LearningJourney).filter_by(
        user_id=user_id, subject_id=subject.id
    ).first()
    if journey is None:
        journey = LearningJourney(user_id=user_id, subject_id=subject.id)
        db.add(journey)
        db.commit()

    # 建立已完成的 Resource
    resource = Resource(
        user_id=user_id,
        subject_id=subject.id,
        name=filename,
        type=ResourceType.PDF,
        status=ResourceStatus.COMPLETED,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)

    context.ids["last_resource_id"] = str(resource.id)
    context.memo["last_resource"] = resource

    # 建立知識節點樹（根節點 + 子節點）
    root_node = KnowledgeNode(
        resource_id=resource.id,
        parent_id=None,
        name="AWS SAA 核心知識",
        depth=0,
        sort_order=0,
    )
    db.add(root_node)
    db.commit()
    db.refresh(root_node)

    child1 = KnowledgeNode(
        resource_id=resource.id,
        parent_id=root_node.id,
        name="EC2 運算服務",
        depth=1,
        sort_order=0,
        source_page_number=12,
        source_text="Amazon EC2 提供可擴展的運算能力...",
    )
    child2 = KnowledgeNode(
        resource_id=resource.id,
        parent_id=root_node.id,
        name="S3 儲存服務",
        depth=1,
        sort_order=1,
        source_page_number=25,
        source_text="Amazon S3 是一種物件儲存服務...",
    )
    db.add(child1)
    db.commit()
    db.add(child2)
    db.commit()
