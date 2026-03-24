"""Behave 環境設定 - Unit Testing with FakeRepository。

此檔案管理 Unit Test 的整個生命週期：
- before_scenario: 初始化 context 狀態、FakeRepository、Services
- after_scenario: 清理狀態
"""

import os
import sys
from types import SimpleNamespace

# 確保專案根目錄在 Python path 中
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def before_scenario(context, scenario):
    """每個 Scenario 執行前初始化。"""
    # 初始化狀態
    context.last_error = None
    context.query_result = None
    context.ids = {}
    context.memo = {}

    # 初始化 Repositories（使用 FakeRepository）
    context.repos = SimpleNamespace()
    # 範例：
    # from {{PY_APP_MODULE}}.repositories.fake_some_repository import FakeSomeRepository
    # context.repos.some = FakeSomeRepository()

    # 初始化 Services
    context.services = SimpleNamespace()
    # 範例：
    # from {{PY_APP_MODULE}}.services.some_service import SomeService
    # context.services.some = SomeService(context.repos.some)


def after_scenario(context, scenario):
    """每個 Scenario 執行後清理。"""
    context.last_error = None
    context.query_result = None
    context.ids.clear()
    context.memo.clear()
