"""Core 模組 - 路徑管理、設定、依賴注入。"""

from {{PY_APP_MODULE}}.core.config import paths, get_settings, Settings, Paths
from {{PY_APP_MODULE}}.core.deps import get_db, set_session_factory

__all__ = [
    "paths",
    "get_settings",
    "Settings",
    "Paths",
    "get_db",
    "set_session_factory",
]
