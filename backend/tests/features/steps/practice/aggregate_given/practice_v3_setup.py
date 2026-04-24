"""Given 練習 V3 通用 fixture — Feature 07 Rule 488。

委派給 node_mastery_setup 使用固定節點名稱 "V3 測試節點"。
"""

from behave import given

from .node_mastery_setup import step_user_node_mastery


@given('使用者 "{email}" 的節點掌握度為 {rate:d}%')
def step_user_default_node_mastery(context, email, rate):
    step_user_node_mastery(context, email, "V3 測試節點", rate)
