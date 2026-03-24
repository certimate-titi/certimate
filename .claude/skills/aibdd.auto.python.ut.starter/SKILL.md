---
name: aibdd.auto.python.ut.starter
description: Python Unit Test Walking Skeleton 初始化。從 templates/ 讀取所有樣板檔案，填入專案參數後輸出到專案目錄，建立 Behave + FakeRepository 的純 Unit Test 骨架（無 DB、無 HTTP）。
user-invocable: true
args-config: arguments-template.yml
argument-hint: "[project-root]"
input: 專案根目錄路徑 + arguments.yml 參數
output: 完整的 Python Unit Test 專案骨架（可直接 pip install + behave 執行）
---

# 角色

Walking Skeleton 建構器。你從 templates/ 讀取樣板，替換 placeholder，寫入專案目錄。

---

# Placeholder 說明

| Placeholder | 來源 | 說明 | 範例 |
|-------------|------|------|------|
| `{{PROJECT_NAME}}` | 詢問使用者 | 專案顯示名稱 | `課程平台` |
| `{{PROJECT_DESCRIPTION}}` | 詢問使用者 | 專案描述 | `BDD Workshop - Python Unit Test` |
| `{{PY_APP_DIR}}` | arguments.yml | Python 應用程式目錄名 | `app` |
| `{{PY_APP_MODULE}}` | 從 PY_APP_DIR 推導 | Python module 路徑 | `app` |
| `{{PY_TEST_MODULE}}` | 從 PY_TEST_FEATURES_DIR 推導 | 測試 module 路徑 | `tests.features` |
| `{{PY_TEST_FEATURES_DIR}}` | arguments.yml | 測試 features 目錄路徑 | `tests/features` |

---

# 執行流程

## Step 1：收集參數

1. 讀取 `${PROJECT_ROOT}/specs/arguments.yml`
2. 詢問使用者：PROJECT_NAME、PROJECT_DESCRIPTION
3. 推導：PY_APP_MODULE、PY_TEST_MODULE

## Step 2：建立目錄結構

```
${PROJECT_ROOT}/
├── ${PY_APP_DIR}/
│   ├── models/
│   ├── repositories/
│   └── services/
├── ${PY_TEST_FEATURES_DIR}/
│   └── steps/
│       └── common_then/
└── ${SPECS_ROOT_DIR}/
    ├── activities/
    ├── features/
    └── clarify/
```

## Step 3：讀取 templates，替換 placeholder，寫入專案

| Template 檔案 | 輸出路徑 |
|---------------|----------|
| [templates/requirements.txt](templates/requirements.txt) | `requirements.txt` |
| [templates/pyproject.toml](templates/pyproject.toml) | `pyproject.toml` |
| [templates/behave.ini](templates/behave.ini) | `behave.ini` |
| [templates/app__init__.py](templates/app__init__.py) | `${PY_APP_DIR}/__init__.py` |
| [templates/app__exceptions.py](templates/app__exceptions.py) | `${PY_APP_DIR}/exceptions.py` |
| [templates/tests__features__environment.py](templates/tests__features__environment.py) | `${PY_TEST_FEATURES_DIR}/environment.py` |
| [templates/tests__features__steps__init__.py](templates/tests__features__steps__init__.py) | `${PY_TEST_FEATURES_DIR}/steps/__init__.py` |
| [templates/tests__features__steps__common_then__init__.py](templates/tests__features__steps__common_then__init__.py) | `${PY_TEST_FEATURES_DIR}/steps/common_then/__init__.py` |
| [templates/tests__features__steps__common_then__success.py](templates/tests__features__steps__common_then__success.py) | `${PY_TEST_FEATURES_DIR}/steps/common_then/success.py` |
| [templates/tests__features__steps__common_then__failure.py](templates/tests__features__steps__common_then__failure.py) | `${PY_TEST_FEATURES_DIR}/steps/common_then/failure.py` |
| [templates/tests__features__steps__common_then__failure_with_reason.py](templates/tests__features__steps__common_then__failure_with_reason.py) | `${PY_TEST_FEATURES_DIR}/steps/common_then/failure_with_reason.py` |
| [templates/tests__features__steps__common_then__error_message.py](templates/tests__features__steps__common_then__error_message.py) | `${PY_TEST_FEATURES_DIR}/steps/common_then/error_message.py` |

## Step 4：建立空 `__init__.py`

- `${PY_APP_DIR}/models/__init__.py`
- `${PY_APP_DIR}/repositories/__init__.py`
- `${PY_APP_DIR}/services/__init__.py`

## Step 5：驗證

確認所有檔案已寫入、無殘留 `{{PLACEHOLDER}}`。

---

# 與 E2E 的差異

| 項目 | E2E | Unit Test |
|------|-----|-----------|
| DB | PostgreSQL（Testcontainers） | 無（FakeRepository，dict-based） |
| HTTP | FastAPI TestClient | 無（直接呼叫 Service） |
| Alembic | 有 | 無 |
| Docker | 有（docker-compose.yml） | 無 |
| JWT | 有（jwt_helper.py） | 無 |
| app/core/ | 有（config, deps） | 無 |
| app/api/ | 有（FastAPI routers） | 無 |

---

# 安全規則

- **不覆蓋已存在的檔案**。
- **不建立 feature-specific 的程式碼**。
- **不執行 pip install**。

---

# 完成後引導

```
Walking skeleton 已建立完成。

產出的檔案：（列出所有檔案）

下一步：
1. cd {{PROJECT_ROOT}} && pip install -r requirements.txt
2. /aibdd.discovery — 開始需求探索
```
