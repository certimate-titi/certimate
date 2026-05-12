"""Given setup — Feature 46 enqueue failure BDD."""

import os
import uuid

from behave import given

from app.models.resource import Resource


@given('環境變數 BACKGROUND_PROCESSOR={mode}')
def step_set_processor_mode(context, mode):
    """設環境變數 + 記住原值給 after_scenario 還原。"""
    if "_env_backup" not in context.memo:
        context.memo["_env_backup"] = {}
    if "BACKGROUND_PROCESSOR" not in context.memo["_env_backup"]:
        context.memo["_env_backup"]["BACKGROUND_PROCESSOR"] = os.environ.get(
            "BACKGROUND_PROCESSOR"
        )
    os.environ["BACKGROUND_PROCESSOR"] = mode


@given('環境變數 WORKER_SERVICE_URL 未設定')
def step_unset_worker_url(context):
    if "_env_backup" not in context.memo:
        context.memo["_env_backup"] = {}
    if "WORKER_SERVICE_URL" not in context.memo["_env_backup"]:
        context.memo["_env_backup"]["WORKER_SERVICE_URL"] = os.environ.get(
            "WORKER_SERVICE_URL"
        )
    os.environ.pop("WORKER_SERVICE_URL", None)




@given('用戶 alice 已建立資源 "{res_name}" status="{status}"')
def step_create_resource_with_status(context, res_name, status):
    from tests.features.steps.sm2.aggregate_given.setup import (
        _ensure_user, _ensure_subject,
    )
    db = context.db_session
    user_id = _ensure_user(db, "alice@example.com")
    if not hasattr(context, "ids"):
        context.ids = {}
    context.ids["alice@example.com"] = str(user_id)
    subject_id = _ensure_subject(db)

    res = Resource(
        user_id=user_id,
        subject_id=subject_id,
        name=res_name,
        type="youtube",
        status=status,
        youtube_url="https://www.youtube.com/watch?v=DUMMY",
        gcs_path="",
        file_size_bytes=0,
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    context.memo["last_resource"] = res
    context.memo["last_resource_id"] = str(res.id)
    context.memo["last_user_id"] = user_id
