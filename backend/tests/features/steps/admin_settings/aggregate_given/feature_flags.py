"""Given 系統中有以下 Feature Flag — Aggregate Given"""

from behave import given

from app.models.feature_flag import FeatureFlag


@given('系統中有以下 Feature Flag：')
def step_impl(context):
    db = context.db_session

    for row in context.table:
        flag_id = row["Flag ID"]
        flag = FeatureFlag(
            flag_key=row["Flag Key"],
            enabled=row["狀態"].lower() == "true",
            rollout_percentage=int(row["上線比例"]),
        )
        db.add(flag)
        db.flush()
        # Store feature flag ID mapping
        context.ids[f"flag_{flag_id}"] = str(flag.id)
        context.ids[f"flag_key_{row['Flag Key']}"] = str(flag.id)

    db.commit()
