"""Then Feature Flag 應為啟用狀態 / 上線比例應為 — Aggregate Then"""

from behave import then

from app.models.feature_flag import FeatureFlag


@then('Feature Flag "{flag_key}" 應為啟用狀態')
def step_impl_enabled(context, flag_key):
    db = context.db_session
    db.expire_all()
    flag = db.query(FeatureFlag).filter(FeatureFlag.flag_key == flag_key).first()
    assert flag is not None, f"找不到 Feature Flag '{flag_key}'"
    assert flag.enabled is True, f"Feature Flag '{flag_key}' 應為啟用狀態，實際 {flag.enabled}"


@then('上線比例應為 {expected:d}')
def step_impl_rollout(context, expected):
    db = context.db_session
    db.expire_all()
    # Get the most recently updated flag
    flags = db.query(FeatureFlag).all()
    assert len(flags) > 0, "找不到任何 Feature Flag"
    latest = flags[-1]
    assert latest.rollout_percentage == expected, \
        f"上線比例應為 {expected}，實際 {latest.rollout_percentage}"
