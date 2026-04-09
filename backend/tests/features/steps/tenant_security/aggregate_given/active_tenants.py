"""Background: 系統已有兩個活躍租戶."""

import uuid
from behave import given
from app.models.tenant import Tenant
from app.models.user import User
from app.repositories.tenant_repository import TenantRepository
from app.repositories.user_repository import UserRepository


@given("系統已有兩個活躍租戶")
def step_impl(context):
    """建立 Background 中的兩個租戶（從 DataTable 讀取）。"""
    tenant_repo = TenantRepository(context.db_session)

    for row in context.table:
        slug = row["slug"]
        name = row["name"]
        plan_tier = row["plan_tier"]

        existing = tenant_repo.find_by_slug(slug)
        if existing:
            context.ids[slug] = str(existing.id)
            continue

        tenant = Tenant(
            id=uuid.uuid4(),
            slug=slug,
            name=name,
            plan_tier=plan_tier,
            is_active=True,
        )
        tenant_repo.save(tenant)
        context.ids[slug] = str(tenant.id)
