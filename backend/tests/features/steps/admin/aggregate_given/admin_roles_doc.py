"""Given 系統中有以下管理角色 — no-op step."""

from behave import given


@given('系統中有以下管理角色：')
def step_admin_roles(context):
    """This step is documentation-only; no DB setup needed."""
    pass


@given('系統中有以下管理角色說明（僅文件用途）')
def step_admin_roles_doc(context):
    """This step is documentation-only; no DB setup needed."""
    pass
