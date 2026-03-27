"""Then 考試倒數相關 — Readmodel Then"""

from behave import then


@then('回應中的考試倒數應對應 "{subject_name}" 的考試日期 {exam_date}')
def step_impl(context, subject_name, exam_date):
    data = context.last_response.json()
    exam_countdown = data.get("exam_countdown", {})
    assert exam_countdown.get("exam_date") == exam_date, \
        f"期望考試日期 '{exam_date}'，實際：{exam_countdown}"


@then('回應中的雷達圖應對應 "{subject_name}" 的能力分布')
def step_impl_radar(context, subject_name):
    data = context.last_response.json()
    radar = data.get("radar_chart")
    assert radar is not None, f"回應中缺少 radar_chart，實際：{data}"
    assert radar.get("subject") == subject_name, \
        f"期望雷達圖科目為 '{subject_name}'，實際：{radar}"
