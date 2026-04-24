"""Given 錯題複習起始 mastery — 委派至 node_mastery_setup。"""

from behave import given

from tests.features.steps.practice.aggregate_given.node_mastery_setup import (
    step_user_node_mastery,
)


@given('使用者 "{email}" 在節點 "{node_name}" 原本的 mastery_rate 為 {rate:d}')
def step_wrong_review_initial_mastery(context, email, node_name, rate):
    step_user_node_mastery(context, email, node_name, rate)
