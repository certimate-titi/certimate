"""Given 系統中有以下內容檢舉 — Aggregate Given"""

import uuid

from behave import given

from app.models.content_report import ContentReport, ReportStatus
from app.models.resource import Resource, ResourceType, ResourceScope, ResourceStatus
from app.models.subject import Subject, SubjectCategory


def _ensure_stub_subject(db, context):
    """Create a stub subject (and category) for resource FK, reuse if exists."""
    memo_key = "__stub_subject_id"
    if memo_key in context.memo:
        return context.memo[memo_key]

    category = SubjectCategory(name="test-category")
    db.add(category)
    db.flush()

    subject = Subject(
        name="test-subject",
        category_id=category.id,
    )
    db.add(subject)
    db.flush()
    context.memo[memo_key] = subject.id
    return subject.id


@given('系統中有以下內容檢舉：')
def step_impl(context):
    db = context.db_session

    for row in context.table:
        report_ref = row["檢舉 ID"]
        reporter_id = row["檢舉者 ID"]
        report_type = row["類型"]
        target_type = row["目標類型"]
        target_id_raw = row["目標 ID"]
        status_raw = row["狀態"]

        status_map = {
            "pending": ReportStatus.PENDING,
            "resolved": ReportStatus.RESOLVED,
            "dismissed": ReportStatus.DISMISSED,
        }

        # If target_type is "resource", create a stub resource so
        # resolve_report can soft-delete it later.
        resource_uuid = None
        if target_type == "resource":
            # Pick the first user from context.ids as the resource owner
            owner_id_str = context.ids.get("1") or context.ids.get("2")
            if not owner_id_str:
                # Fallback: use any user id from context.ids
                for v in context.ids.values():
                    owner_id_str = v
                    break

            subject_id = _ensure_stub_subject(db, context)

            resource_uuid = uuid.uuid4()
            resource = Resource(
                id=resource_uuid,
                user_id=uuid.UUID(owner_id_str),
                subject_id=subject_id,
                name=f"test-resource-{target_id_raw}",
                type=ResourceType.PDF,
                scope=ResourceScope.PERSONAL,
                status=ResourceStatus.COMPLETED,
            )
            db.add(resource)
            db.flush()
            context.ids[f"resource_{target_id_raw}"] = str(resource_uuid)

        # Store resource UUID string as target_id so the service can look it up
        target_id_value = str(resource_uuid) if resource_uuid else target_id_raw

        report = ContentReport(
            report_ref=report_ref,
            reporter_id=reporter_id,
            report_type=report_type,
            target_type=target_type,
            target_id=target_id_value,
            status=status_map.get(status_raw, ReportStatus.PENDING),
        )
        db.add(report)
        db.flush()
        context.ids[report_ref] = str(report.id)

    db.commit()
