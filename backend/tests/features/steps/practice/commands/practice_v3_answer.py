"""When 練習模式答對一題 — Feature 07 Rule 488（無節點參數）。"""

from behave import when

from .practice_correct_answer import step_practice_answer_correctly


@when('使用者在練習模式答對一題')
def step_practice_answer_default(context):
    step_practice_answer_correctly(context, "V3 測試節點")
