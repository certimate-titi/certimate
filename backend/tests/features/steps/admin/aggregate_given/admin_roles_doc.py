"""Given 系統中有以下管理角色說明（僅文件用途） — no-op step."""

from behave import given


@given('系統中有以下管理角色說明（僅文件用途）')
def step_impl(context):
    """This step is documentation-only; no DB setup needed."""
    pass
