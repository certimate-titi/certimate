---
name: aibdd.auto.python.e2e.starter
description: Python E2E Walking Skeleton 初始化。從 templates/ 讀取所有樣板檔案，填入專案參數後輸出到專案目錄，建立完整的 FastAPI + SQLAlchemy + Behave + Testcontainers 骨架。
user-invocable: true
args-config: arguments-template.yml
argument-hint: "[project-root]"
input: 專案根目錄路徑 + arguments.yml 參數
output: 完整的 Python E2E 專案骨架（可直接 pip install + behave 執行）
---

# 角色

Walking Skeleton 建構器。你從 templates/ 讀取樣板，替換 placeholder，寫入專案目錄。

---

# Placeholder 說明

所有 template 檔案使用 `{{PLACEHOLDER}}` 格式。以下是需要替換的變數：

| Placeholder | 來源 | 說明 | 範例 |
|-------------|------|------|------|
| `{{PROJECT_NAME}}` | 詢問使用者 | 專案顯示名稱 | `課程平台` |
| `{{PROJECT_DESCRIPTION}}` | 詢問使用者 | 專案描述 | `BDD Workshop - Python E2E` |
| `{{PROJECT_SLUG}}` | 從 PROJECT_NAME 推導 | URL-safe 識別碼（小寫、連字號） | `course-platform` |
| `{{PY_APP_DIR}}` | arguments.yml | Python 應用程式目錄名 | `app` |
| `{{PY_APP_MODULE}}` | 從 PY_APP_DIR 推導 | Python module 路徑（`.` 分隔） | `app` |
| `{{PY_TEST_MODULE}}` | 從 PY_TEST_FEATURES_DIR 推導 | 測試 module 路徑（`.` 分隔） | `tests.features` |
| `{{PY_TEST_FEATURES_DIR}}` | arguments.yml | 測試 features 目錄路徑 | `tests/features` |
| `{{SPECS_ROOT_DIR}}` | arguments.yml | 規格檔案根目錄 | `specs` |

---

# 執行流程

## Step 1：收集參數

1. 讀取 `${PROJECT_ROOT}/specs/arguments.yml`（由 `/aibdd.kickoff` 產出）
2. 詢問使用者：
   - `PROJECT_NAME`：專案顯示名稱
   - `PROJECT_DESCRIPTION`：專案描述（建議預設值）
3. 推導：
   - `PROJECT_SLUG` = PROJECT_NAME 轉小寫、空格換連字號、移除特殊字元
   - `PY_APP_MODULE` = PY_APP_DIR（`/` 換成 `.`）
   - `PY_TEST_MODULE` = PY_TEST_FEATURES_DIR（`/` 換成 `.`）

## Step 2：建立目錄結構

根據 arguments.yml 建立所有目錄：

```
${PROJECT_ROOT}/
├── ${PY_APP_DIR}/
│   ├── core/
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── api/
│   └── schemas/
├── ${PY_TEST_FEATURES_DIR}/
│   ├── helpers/
│   └── steps/
│       └── common_then/
├── alembic/
│   └── versions/
└── ${SPECS_ROOT_DIR}/
    ├── activities/
    ├── features/
    └── clarify/
```

## Step 3：讀取 templates，替換 placeholder，寫入專案

**檔案名對照表**（template 檔名用 `__` 表示目錄分隔符 `/`）：

| Template 檔案 | 輸出路徑 |
|---------------|----------|
| [templates/requirements.txt](templates/requirements.txt) | `requirements.txt` |
| [templates/pyproject.toml](templates/pyproject.toml) | `pyproject.toml` |
| [templates/behave.ini](templates/behave.ini) | `behave.ini` |
| [templates/docker-compose.yml](templates/docker-compose.yml) | `docker-compose.yml` |
| [templates/alembic.ini](templates/alembic.ini) | `alembic.ini` |
| [templates/app__init__.py](templates/app__init__.py) | `${PY_APP_DIR}/__init__.py` |
| [templates/app__main.py](templates/app__main.py) | `${PY_APP_DIR}/main.py` |
| [templates/app__exceptions.py](templates/app__exceptions.py) | `${PY_APP_DIR}/exceptions.py` |
| [templates/app__core__init__.py](templates/app__core__init__.py) | `${PY_APP_DIR}/core/__init__.py` |
| [templates/app__core__config.py](templates/app__core__config.py) | `${PY_APP_DIR}/core/config.py` |
| [templates/app__core__deps.py](templates/app__core__deps.py) | `${PY_APP_DIR}/core/deps.py` |
| [templates/app__models__init__.py](templates/app__models__init__.py) | `${PY_APP_DIR}/models/__init__.py` |
| [templates/app__api__init__.py](templates/app__api__init__.py) | `${PY_APP_DIR}/api/__init__.py` |
| [templates/alembic__env.py](templates/alembic__env.py) | `alembic/env.py` |
| [templates/tests__features__environment.py](templates/tests__features__environment.py) | `${PY_TEST_FEATURES_DIR}/environment.py` |
| [templates/tests__features__helpers__init__.py](templates/tests__features__helpers__init__.py) | `${PY_TEST_FEATURES_DIR}/helpers/__init__.py` |
| [templates/tests__features__helpers__jwt_helper.py](templates/tests__features__helpers__jwt_helper.py) | `${PY_TEST_FEATURES_DIR}/helpers/jwt_helper.py` |
| [templates/tests__features__steps__init__.py](templates/tests__features__steps__init__.py) | `${PY_TEST_FEATURES_DIR}/steps/__init__.py` |
| [templates/tests__features__steps__common_then__init__.py](templates/tests__features__steps__common_then__init__.py) | `${PY_TEST_FEATURES_DIR}/steps/common_then/__init__.py` |
| [templates/tests__features__steps__common_then__success.py](templates/tests__features__steps__common_then__success.py) | `${PY_TEST_FEATURES_DIR}/steps/common_then/success.py` |
| [templates/tests__features__steps__common_then__failure.py](templates/tests__features__steps__common_then__failure.py) | `${PY_TEST_FEATURES_DIR}/steps/common_then/failure.py` |
| [templates/tests__features__steps__common_then__failure_with_reason.py](templates/tests__features__steps__common_then__failure_with_reason.py) | `${PY_TEST_FEATURES_DIR}/steps/common_then/failure_with_reason.py` |
| [templates/tests__features__steps__common_then__error_message.py](templates/tests__features__steps__common_then__error_message.py) | `${PY_TEST_FEATURES_DIR}/steps/common_then/error_message.py` |

## Step 4：建立空 `__init__.py`

為以下目錄建立空的 `__init__.py`（不需要 template）：

- `${PY_APP_DIR}/repositories/__init__.py`
- `${PY_APP_DIR}/services/__init__.py`
- `${PY_APP_DIR}/schemas/__init__.py`

## Step 5：驗證

完成後列出所有產出的檔案，確認：
1. 所有 template 都已寫入
2. 所有 `{{PLACEHOLDER}}` 都已替換（不應有殘留）
3. 目錄結構完整

---

# 安全規則

- **不覆蓋已存在的檔案**。若目標檔案已存在，跳過並回報。
- **不建立 feature-specific 的程式碼**（models、repositories、services、API endpoints、step definitions）。那些是 automation skills 的職責。
- **不執行 pip install 或 alembic init**。骨架建完後，使用者自行安裝。

---

# 完成後引導

```
Walking skeleton 已建立完成。

產出的檔案：（列出所有檔案）

下一步：
1. cd {{PROJECT_ROOT}} && pip install -r requirements.txt
2. /aibdd.discovery — 開始需求探索
```
