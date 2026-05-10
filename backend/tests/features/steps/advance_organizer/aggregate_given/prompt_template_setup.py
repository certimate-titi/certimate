"""Given 前置條件 — prompt template seed 相關 (Feature 41)."""

from behave import given


@given("DB K-06 v{version:d} 內容與 file v{version2:d} 相同")
def step_given_db_k06_same_as_file(context, version, version2):
    """前置條件：DB K-06 已存在且與 file 版本相同（hash match 場景）。

    BDD 層確認邏輯存在即可；詳細 hash 驗證由 seed_prompts unit test 覆蓋。
    """
    context.memo["seed_scenario"] = "hash_match"
    context.memo["k06_file_version"] = version2


@given("DB K-06 v{version:d} 內容（無 retrieval_prompt schema）")
def step_given_db_k06_old_content(context, version):
    """前置條件：DB K-06 使用舊版內容（hash mismatch 場景）。"""
    context.memo["seed_scenario"] = "hash_mismatch"
    context.memo["k06_db_version"] = version


@given("file K-06 v{version:d} 內容（含 retrieval_prompt schema）")
def step_given_file_k06_new_content(context, version):
    """前置條件：file K-06 使用新版內容（hash mismatch 場景）。"""
    context.memo["k06_file_version"] = version
