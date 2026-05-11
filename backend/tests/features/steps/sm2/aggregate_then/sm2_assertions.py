"""SM-2 排程結果斷言 — Feature 42 BDD."""

from datetime import datetime, timezone

from behave import then


def _interval_days_diff(target: datetime, expected_days: int) -> float:
    """回傳 next_review_at 與「今天 + expected_days」相差幾天（可正負）。"""
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return (target - now).total_seconds() / 86400 - expected_days


@then('SM-2 排程 next_review_at = today + {days:d}d, repetitions = {reps:d}, '
      'ease_factor ≈ {ef:f}')
def step_assert_sm2_state(context, days, reps, ef):
    sched = context.memo["last_sched"]
    diff = _interval_days_diff(sched.next_review_at, days)
    assert abs(diff) < 0.5, (
        f"next_review_at 偏離預期 {days} 天 {diff:+.2f} 天"
    )
    assert sched.repetitions == reps, (
        f"預期 repetitions={reps}，實際={sched.repetitions}"
    )
    assert abs(float(sched.ease_factor) - ef) < 0.05, (
        f"預期 ease_factor≈{ef}，實際={sched.ease_factor}"
    )
    assert int(sched.interval_days) == days, (
        f"預期 interval_days={days}，實際={sched.interval_days}"
    )


@then('next_review_at = today + {days:d}d, repetitions = {reps:d}, '
      'ease_factor ≈ {ef:f}')
def step_assert_sm2_state_compact(context, days, reps, ef):
    """次次複習用的簡寫版（無 SM-2 排程前綴）。"""
    step_assert_sm2_state(context, days, reps, ef)


@then('next_review_at = today + {days:d}d (round({base:d} * {ef:f})), '
      'repetitions = {reps:d}')
def step_assert_sm2_state_with_formula(context, days, base, ef, reps):
    """測 interval = round(base * ef) 的公式版本。"""
    sched = context.memo["last_sched"]
    diff = _interval_days_diff(sched.next_review_at, days)
    assert abs(diff) < 0.5, (
        f"next_review_at 偏離預期 {days} 天 {diff:+.2f} 天"
    )
    assert sched.repetitions == reps, (
        f"預期 repetitions={reps}，實際={sched.repetitions}"
    )
    assert int(sched.interval_days) == days, (
        f"預期 interval_days={days}，實際={sched.interval_days}"
    )


@then('next_review_at = today + {days:d}d, repetitions = {reps:d}, '
      'ease_factor 下降至 ~{ef:f}')
def step_assert_sm2_drop(context, days, reps, ef):
    sched = context.memo["last_sched"]
    diff = _interval_days_diff(sched.next_review_at, days)
    assert abs(diff) < 0.5, (
        f"next_review_at 偏離預期 {days} 天 {diff:+.2f} 天"
    )
    assert sched.repetitions == reps, (
        f"預期 repetitions={reps}，實際={sched.repetitions}"
    )
    assert abs(float(sched.ease_factor) - ef) < 0.1, (
        f"預期 ease_factor≈{ef}，實際={sched.ease_factor}"
    )


@then('ease_factor 不會降到 {floor:f} 以下')
def step_assert_ease_factor_floor(context, floor):
    sched = context.memo["last_sched"]
    assert float(sched.ease_factor) >= floor, (
        f"預期 ease_factor>={floor}，實際={sched.ease_factor}"
    )
