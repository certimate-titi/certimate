"""Then DB-level assertion for soft-hide via user_hidden_resources."""

from behave import then
from sqlalchemy import text


def _resolve(context, alias):
    return context.ids.get(alias) or alias


@then('資料庫中 user_hidden_resources 應有 user_id 為 "{user_alias}" 且 resource_id 為 {res_alias} 的 row')
def step_hidden_row(context, user_alias, res_alias):
    uid = _resolve(context, user_alias)
    rid = _resolve(context, res_alias)
    row = context.db_session.execute(
        text(
            "SELECT 1 FROM user_hidden_resources "
            "WHERE user_id = :uid AND resource_id = :rid"
        ),
        {"uid": uid, "rid": rid},
    ).fetchone()
    assert row is not None, (
        f"user_hidden_resources 缺 (user={user_alias}/{uid}, resource={res_alias}/{rid})"
    )
