"""Given — alice 在科目下有多個 resource 各自寫了 user_response（Feature 50 subject-level scaffolds）。"""

import uuid

from behave import given

from app.models.resource import Resource
from app.models.resource_scaffold import ResourceScaffold, ResourceScaffoldType


@given("alice 在科目下有 resource1 寫了 1 筆 user_response、resource2 寫了 2 筆 user_response")
def step_alice_two_resources_with_user_responses(context):
    """建立 2 個 resource，分別寫 1 筆、2 筆有 user_response 的 scaffold。"""
    from datetime import datetime, timezone

    db = context.db_session
    user_id = uuid.UUID(context.ids["alice@example.com"])
    subject_id = uuid.UUID(context.memo["subject_id"])

    # Resource 1 — 1 筆 user_response
    r1 = Resource(
        user_id=user_id,
        subject_id=subject_id,
        name="F50-SubjScaffold-R1",
        type="pdf",
        status="COMPLETED",
        file_size_bytes=1024,
        gcs_path="test/f50_r1.pdf",
    )
    db.add(r1)
    db.flush()

    s1 = ResourceScaffold(
        resource_id=r1.id,
        type=ResourceScaffoldType.ELABORATIVE,
        content="resource1 鷹架內容",
        user_response="resource1 的深讀回應",
        responded_at=datetime.now(timezone.utc),
    )
    db.add(s1)

    # Resource 2 — 2 筆 user_response
    r2 = Resource(
        user_id=user_id,
        subject_id=subject_id,
        name="F50-SubjScaffold-R2",
        type="pdf",
        status="COMPLETED",
        file_size_bytes=2048,
        gcs_path="test/f50_r2.pdf",
    )
    db.add(r2)
    db.flush()

    for i in range(2):
        s = ResourceScaffold(
            resource_id=r2.id,
            type=ResourceScaffoldType.ELABORATIVE,
            content=f"resource2 鷹架內容 {i + 1}",
            user_response=f"resource2 的深讀回應 {i + 1}",
            responded_at=datetime.now(timezone.utc),
        )
        db.add(s)

    db.commit()
