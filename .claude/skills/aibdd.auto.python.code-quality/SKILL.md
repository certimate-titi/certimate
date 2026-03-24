---
name: aibdd.auto.python.code-quality
description: Python 程式碼品質規範合集。包含 SOLID 設計原則、Step Definition 組織規範、StepDef Meta 註記清理、日誌實踐、程式架構、程式碼品質等六項規範。供 refactor 階段嚴格遵守。
user-invocable: false
---

# SOLID 設計原則

## 目的

確保程式碼好讀、好維護、好擴充。重構時必須遵守這些原則。

---

## S - Single Responsibility Principle（單一職責原則）

每個類別/函式只負責一件事。

**範例：**
```python
# ❌ Service 做太多事
class AssignmentService:
    def submit_assignment(self, user_id, content):
        # 驗證權限
        if not self._check_permission(user_id):
            raise PermissionError()
        # 驗證內容
        if len(content) < 10:
            raise ValueError()
        # 儲存資料
        self.repository.save(...)
        # 發送通知
        self._send_email(user_id)

# ✅ 職責分離
class AssignmentService:
    def __init__(self, assignment_repo, permission_validator, notification_service):
        self.assignment_repo = assignment_repo
        self.permission_validator = permission_validator
        self.notification_service = notification_service

    def submit_assignment(self, user_id, content):
        self.permission_validator.validate(user_id)  # 權限驗證交給專門的類別
        assignment = Assignment(user_id=user_id, content=content)
        self.assignment_repo.save(assignment)
        self.notification_service.notify(user_id)  # 通知交給專門的服務
```

---

## O - Open/Closed Principle（開放封閉原則）

對擴展開放，對修改封閉。新增功能時應透過擴展而非修改現有程式碼。

---

## L - Liskov Substitution Principle（里氏替換原則）

子類別應該可以替換父類別而不影響程式正確性。

---

## I - Interface Segregation Principle（介面隔離原則）

不應強迫客戶端依賴它不需要的介面。

---

## D - Dependency Inversion Principle（依賴反轉原則）

高層模組不應依賴低層模組，兩者都應依賴抽象。

**範例：**
```python
# ✅ Service 透過建構子注入 Repository
class LessonProgressService:
    def __init__(self, lesson_progress_repo, journey_subscription_repo):
        self.lesson_progress_repo = lesson_progress_repo
        self.journey_subscription_repo = journey_subscription_repo

    def update_progress(self, user_id, lesson_id, progress):
        # 業務邏輯使用注入的 repository
        subscription = self.journey_subscription_repo.find_by_user(user_id)
        if not subscription:
            raise SubscriptionNotFoundError()
        # ...
```

---

## 檢查清單

- [ ] 每個類別/函式只負責一件事
- [ ] Service 透過建構子注入 Repository
- [ ] 高層模組不直接依賴低層模組

---

# Step Definition 組織規範

## 目的

確保 Behave Step Definition 檔案組織清晰、易於維護。

---

## 組織原則

- 一個 Step Pattern 對應一個 Python module
- 使用目錄分類（`aggregate_given/`, `commands/`, `query/` 等）
- 語意化檔名（避免 `steps.py` 這類大雜燴）

---

## 目錄結構範例

```
tests/features/steps/
├── __init__.py              # 匯入所有 step modules
├── aggregate_given/         # Given: 建立 Aggregate 狀態
│   ├── __init__.py
│   ├── lesson_progress.py
│   ├── user.py
│   └── journey.py
├── commands/                # When: 執行 Command
│   ├── __init__.py
│   ├── update_video_progress.py
│   └── subscribe_journey.py
├── query/                   # When: 執行 Query
│   ├── __init__.py
│   └── get_lesson_progress.py
├── aggregate_then/          # Then: 驗證 Aggregate 狀態
│   ├── __init__.py
│   └── lesson_progress.py
├── readmodel_then/          # Then: 驗證 ReadModel 結果
│   ├── __init__.py
│   └── progress_result.py
├── common_then/             # Then: 通用驗證（成功/失敗）
│   ├── __init__.py
│   ├── success.py
│   └── failure.py
└── helpers/                 # 共用輔助函式
    ├── __init__.py
    ├── status_mapping.py
    └── context_helpers.py
```

---

## __init__.py 匯入規範

`tests/features/steps/__init__.py` 必須匯入所有 step modules，否則 Behave 找不到 step definitions。

```python
# tests/features/steps/__init__.py

# Common Then
from .common_then import success
from .common_then import failure

# Aggregate Given
from .aggregate_given import user
from .aggregate_given import lesson_progress as given_lesson_progress

# Commands
from .commands import update_video_progress

# Aggregate Then
from .aggregate_then import lesson_progress as then_lesson_progress
```

**注意**：若 aggregate_given 和 aggregate_then 有同名模組，需使用別名避免衝突。

---

## 共用邏輯提取

### 狀態映射

```python
# tests/features/helpers/status_mapping.py

STATUS_MAPPING = {
    "進行中": "IN_PROGRESS",
    "已完成": "COMPLETED",
    "未開始": "NOT_STARTED",
}

def map_status(chinese_status: str) -> str:
    """將中文狀態映射為英文 enum"""
    return STATUS_MAPPING.get(chinese_status, chinese_status)
```

### Context 操作

```python
# tests/features/helpers/context_helpers.py

def get_user_id(context, user_name: str) -> str:
    """從 context 取得用戶 ID，若不存在則拋出錯誤"""
    if user_name not in context.ids:
        raise KeyError(f"找不到用戶 '{user_name}' 的 ID")
    return context.ids[user_name]

def store_user_id(context, user_name: str, user_id: str) -> None:
    """儲存用戶 ID 到 context"""
    context.ids[user_name] = user_id
```

---

## 檢查清單

- [ ] 一個 Step Pattern 對應一個 Python module
- [ ] 使用目錄分類組織 step definitions
- [ ] `__init__.py` 已匯入所有 step modules
- [ ] 同名模組使用別名避免衝突
- [ ] 共用邏輯已提取到 `helpers/`

---

# Meta 註記清理規範

## 目的

移除開發過程中的臨時註記，保持程式碼乾淨。

---

## 刪除的內容

- `# TODO: [事件風暴部位: ...]`
- `# TODO: 參考 xxx-Handler.md 實作`
- `# [生成參考 Prompt: ...]`
- 其他開發過程中的臨時標記

---

## 保留的內容

- 必要的業務邏輯註解
- 必要的技術註解（如解釋複雜邏輯）

---

## 範例

**重構前：**
```python
@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    """
    TODO: [事件風暴部位: Aggregate - LessonProgress]
    TODO: 參考 Aggregate-Given-Handler.md 實作
    """
    db_session = context.db_session
    repository = LessonProgressRepository(db_session)

    # 狀態映射
    status_mapping = {...}
    db_status = status_mapping.get(status, status)

    progress_entity = LessonProgress(...)
    repository.save(progress_entity)
    context.ids[user_name] = progress_entity.user_id
```

**重構後：**
```python
@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    db_session = context.db_session
    repository = LessonProgressRepository(db_session)

    # 狀態映射（中文 → 英文 enum）
    status_mapping = {...}
    db_status = status_mapping.get(status, status)

    progress_entity = LessonProgress(...)
    repository.save(progress_entity)
    context.ids[user_name] = progress_entity.user_id
```

---

## 檢查清單

- [ ] 所有 `TODO: [事件風暴部位: ...]` 已刪除
- [ ] 所有 `TODO: 參考 xxx-Handler.md 實作` 已刪除
- [ ] 所有 `[生成參考 Prompt: ...]` 已刪除
- [ ] 必要的業務邏輯註解已保留

---

# 日誌實踐規範

## 目的

本文件定義專案的日誌（Logging）使用規範，確保應用程式在 Docker 容器中運行時具備良好的可觀測性，方便除錯和監控。

---

## 日誌框架

使用 Python 標準庫 `logging` 模組，在每個模組頂部宣告 logger。

```python
# ❌ 直接 print
def create_order(user_id, request):
    print(f"Creating order for user {user_id}")

# ✅ 使用 logging
import logging

logger = logging.getLogger(__name__)

def create_order(user_id, request):
    logger.info("Creating order for userId=%s, items=%d", user_id, len(request.items))
```

---

## 日誌等級使用規則

### ERROR — 系統異常，需要立即關注

用於未預期的錯誤、系統故障。應包含完整 stack trace。

```python
logger.error("Unexpected error: %s", str(ex), exc_info=True)
```

### WARNING — 預期內的異常狀況

用於認證失敗、權限不足、資料解析失敗等可預期但需留意的情況。

```python
logger.warning("Expired JWT token for %s %s", method, path)
logger.warning("Access denied: userId=%s, journeyId=%s", user_id, journey_id)
logger.warning("Failed to parse plan_items for productId=%s: %s", product_id, str(e))
```

### INFO — 業務關鍵操作

用於記錄重要的業務事件，如建立訂單、付款、角色授予等。這是 Docker 容器中最主要的觀測依據。

```python
logger.info("Order created: orderNumber=%s, userId=%s, totalPrice=%s", order_number, user_id, total_price)
logger.info("Payment submitted: orderId=%s, amount=%s, method=%s", order_id, amount, method)
logger.info("Role granted: userId=%s, journeyId=%s, roleType=%s", user_id, journey_id, role_type)
```

### DEBUG — 詳細執行流程

用於開發和除錯時的詳細資訊，如查詢參數、回傳數量等。在生產環境可透過配置關閉。

```python
logger.debug("Fetching order orderNumber=%s for userId=%s", order_number, user_id)
logger.debug("Product list fetched: statusFilter=%s, count=%d", status_filter, len(products))
```

---

## 各層日誌策略

### API 層（Router / Endpoint）

記錄每個 API 請求的進入點，包含關鍵參數（userId、資源 ID 等）。

```python
# app/api/orders.py
import logging
from fastapi import APIRouter, Depends, Request
from app.core.deps import get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/api/v1/orders")
def create_order(request: CreateOrderRequest, current_user_id: int = Depends(get_current_user_id)):
    logger.info("Creating order for userId=%s, items=%d", current_user_id, len(request.items))
    return order_service.create_order(current_user_id, request)
```

**原則**：
- 使用 `logger.info` 記錄請求進入
- 包含 userId 和關鍵業務參數
- 不記錄敏感資訊（密碼、token 全文等）

### Service 層

記錄業務邏輯的關鍵決策點和結果。

```python
# app/services/order_service.py
import logging

logger = logging.getLogger(__name__)

class OrderService:
    def create_order(self, user_id: int, request):
        logger.debug("Creating order for userId=%s", user_id)

        # ... 業務邏輯 ...

        order = self.order_repo.save(order)
        logger.info("Order created: orderNumber=%s, userId=%s, totalPrice=%s, items=%d",
                     order.order_number, user_id, total_price, len(items))

        return response
```

**原則**：
- `logger.info` 用於業務操作完成（寫入操作：建立、更新、刪除）
- `logger.debug` 用於操作開始和查詢結果
- `logger.warning` 用於資料解析失敗等可恢復的異常

### Security 層（Middleware / Dependency）

記錄每個 HTTP 請求和認證結果。

```python
# app/core/deps.py
import logging

logger = logging.getLogger(__name__)

def get_current_user_id(request: Request) -> int:
    logger.info(">>> %s %s", request.method, request.url.path)

    token = request.headers.get("Authorization", "")
    if not token.startswith("Bearer "):
        logger.debug("No Bearer token for %s %s", request.method, request.url.path)
        raise HTTPException(status_code=401, detail="未提供 Token")

    try:
        payload = jwt.decode(token[7:], SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        logger.debug("Authenticated userId=%s for %s %s", user_id, request.method, request.url.path)
        return int(user_id)
    except jwt.ExpiredSignatureError:
        logger.warning("Expired JWT token for %s %s", request.method, request.url.path)
        raise HTTPException(status_code=401, detail="Token 已過期")
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid JWT token for %s %s: %s", request.method, request.url.path, str(e))
        raise HTTPException(status_code=401, detail="無效的 Token")
```

### 全域例外處理

依據 HTTP 狀態碼使用不同日誌等級。

```python
# app/core/exception_handlers.py
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)

async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code >= 500:
        logger.error("Server error [%d]: %s", exc.status_code, exc.detail, exc_info=True)
    elif exc.status_code in (401, 403):
        logger.warning("Auth error [%d]: %s", exc.status_code, exc.detail)
    else:
        logger.info("Client error [%d]: %s", exc.status_code, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})

async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unexpected error: %s", str(exc), exc_info=True)
    return JSONResponse(status_code=500, content={"message": "內部伺服器錯誤"})
```

---

## 日誌格式

使用結構化的 key=value 格式，方便 Docker 容器中用 `grep` 或日誌工具搜尋。

```python
# ❌ 不易搜尋
logger.info(f"使用者 {user_id} 建立了訂單 {order_number}")

# ✅ 結構化 key=value（使用 % 格式化）
logger.info("Order created: orderNumber=%s, userId=%s, totalPrice=%s", order_number, user_id, total_price)
```

**原則**：
- 使用 `%s`、`%d` 佔位符（logging 延遲格式化），不要用 f-string
- 使用 `key=value` 格式記錄參數
- 在訊息前加上簡短的事件描述（如 `Order created:`、`Payment submitted:`）

---

## 日誌配置

在 FastAPI 應用啟動時配置日誌：

```python
# app/core/logging_config.py
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(threadName)s] %(levelname)-5s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # 降低第三方庫的日誌等級
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
```

若需要顯示 SQL 語句（開發除錯）：

```python
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
```

---

## 禁止事項

- ❌ 不要記錄敏感資訊（密碼、JWT token 全文、信用卡號）
- ❌ 不要在迴圈中使用 `logger.info`（改用 `logger.debug` 或在迴圈外記錄彙總）
- ❌ 不要用 `print()` 取代 `logging`
- ❌ 不要用 f-string 格式化日誌訊息（`logger.info(f"msg {var}")`），使用 `%s` 佔位符（`logger.info("msg %s", var)`）

---

## 檢查清單

- [ ] 所有 API、Service、Security 模組宣告 `logger = logging.getLogger(__name__)`
- [ ] API 層每個端點記錄請求進入（`logger.info`）
- [ ] Service 層寫入操作完成時記錄（`logger.info`）
- [ ] Service 層查詢操作記錄結果數量（`logger.debug`）
- [ ] 認證失敗記錄警告（`logger.warning`）
- [ ] 未預期錯誤記錄完整 stack trace（`logger.error` + `exc_info=True`）
- [ ] 使用 key=value 格式和 `%s` 佔位符
- [ ] 不記錄敏感資訊
- [ ] 配置適當的日誌等級和格式

---

**文件建立日期**：2026-01-26
**文件版本**：E2E Cucumber BDD Version 1.0
**適用框架**：Python 3.11+ + FastAPI + SQLAlchemy

---

# 程式架構規範

## 目的

本文件定義專案的程式碼組織結構、職責分層和檔案擺放規則，適用於所有程式開發階段（紅燈、綠燈、重構）。

---

## 檔案組織結構

### 應用程式程式碼目錄結構（範例）

所有 **Domain Specific** 的程式碼都應該放在 `app/` 正下方的對應目錄中：

```
app/
├── api/                    # API Endpoints / Controllers
│   ├── __init__.py
│   ├── orders.py          # 訂單相關的 API
│   └── products.py        # 商品相關的 API
├── services/               # Business Logic Services
│   ├── __init__.py
│   ├── order_service.py
│   └── inventory_service.py
├── repositories/           # Data Access Layer
│   ├── __init__.py
│   ├── order_repository.py
│   └── product_repository.py
├── models/                 # SQLAlchemy ORM Models
│   ├── __init__.py
│   ├── order.py
│   └── product.py
├── schemas/                # Request/Response Schemas (Pydantic)
│   ├── __init__.py
│   ├── order.py
│   └── product.py
├── core/                   # 核心工具和配置
│   ├── config.py
│   ├── deps.py            # 依賴注入
│   └── security.py        # 認證相關
└── main.py                # FastAPI app 入口
```

### ❌ 錯誤：不要放在 walking_skeleton

`app/walking_skeleton/` **只用於基礎建設驗證**，不應該包含任何 domain specific 的程式碼。

### ✅ 正確：Domain 程式碼放在 app/ 正下方

```python
# ✅ 所有業務相關的程式碼都放在 app/ 的對應目錄下
app/api/orders.py                        # 訂單 API
app/services/order_service.py           # 訂單業務邏輯
app/schemas/order.py                     # 訂單 schemas
app/models/order.py                      # 訂單 Model（紅燈階段已建立）
app/repositories/order_repository.py    # 訂單 Repository（紅燈階段已建立）
```

---

## 分層架構（由外到內）

### Layer 1: Controller / API Endpoints

**職責**：處理 HTTP Request/Response

**負責的事**：
- 定義路由（URL path）
- 解析 HTTP Request（headers, body, query params）
- 呼叫 Service 執行業務邏輯
- 構建 HTTP Response（status code, body）
- 處理認證（驗證 JWT token）

**不負責的事**：
- ❌ 業務邏輯（交給 Service）
- ❌ 資料存取（交給 Repository）

**檔案位置**：`app/api/`

**範例**：
```python
# app/api/orders.py
from fastapi import APIRouter, Depends
from app.services.order_service import OrderService
from app.core.deps import get_current_user_id
from app.schemas.order import CreateOrderRequest

router = APIRouter()

@router.post("/api/orders")
def create_order(request: CreateOrderRequest, current_user_id: int = Depends(get_current_user_id)):
    # 解析 request
    product_id = request.product_id
    quantity = request.quantity

    # 呼叫 service（業務邏輯在這裡）
    service = OrderService()
    order = service.create_order(current_user_id, product_id, quantity)

    # 返回 response
    return {"order_id": order.id, "status": "created"}
```

### Layer 2: Service

**職責**：業務邏輯和規則

**負責的事（用最小的程式碼改動成本來實現以下）**：
- 驗證業務規則
- 執行業務流程
- 協調 Repository 讀寫資料
- 拋出業務異常（如資源不存在、狀態錯誤）

**必須支援依賴注入**：
- 接收 Repository 作為參數
- 讓測試和生產環境可以使用不同的 Repository

**檔案位置**：`app/services/`

**範例**：
```python
# app/services/order_service.py
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.models.order import Order

class OrderService:
    def __init__(self, order_repo: OrderRepository, product_repo: ProductRepository):
        self.order_repo = order_repo
        self.product_repo = product_repo

    def create_order(self, user_id: int, product_id: int, quantity: int):
        # 業務規則：檢查商品是否存在
        product = self.product_repo.find_by_id(product_id)
        if not product:
            raise ProductNotFoundError()

        # 業務規則：檢查庫存是否足夠
        if product.stock < quantity:
            raise InsufficientStockError()

        # 業務邏輯：創建訂單
        order = Order(user_id=user_id, product_id=product_id, quantity=quantity)
        self.order_repo.save(order)

        # 業務邏輯：扣減庫存
        product.stock -= quantity
        self.product_repo.save(product)

        return order
```

### Layer 3: Repository

**職責**：資料存取

**負責的事**：
- 使用 SQLAlchemy 操作真實 PostgreSQL
- 執行 CRUD 操作（Create, Read, Update, Delete）
- 封裝資料庫查詢邏輯

**在綠燈階段**：
- Repository 基本結構在紅燈階段已定義
- 綠燈階段可能需要調整或新增方法

**檔案位置**：`app/repositories/`

**範例**：
```python
# app/repositories/order_repository.py
from sqlalchemy.orm import Session
from app.models.order import Order

class OrderRepository:
    def __init__(self, session: Session):
        self.session = session

    def find_by_id(self, order_id: int):
        return self.session.query(Order).filter_by(id=order_id).first()

    def find_by_user(self, user_id: int):
        return self.session.query(Order).filter_by(user_id=user_id).all()

    def save(self, order: Order):
        self.session.merge(order)
        self.session.commit()
        return order
```

---

## 依賴注入原則

**讓測試環境和生產環境使用同一套程式碼，但可以切換不同的 Repository。**

### 在生產環境
```python
# app/core/deps.py 或 app/main.py
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.services.order_service import OrderService

# 使用真實的 PostgreSQL
order_repo = OrderRepository(production_db_session)
product_repo = ProductRepository(production_db_session)
service = OrderService(order_repo, product_repo)
```

### 在測試環境
```python
# tests/features/environment.py 或 step definitions 中
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.services.order_service import OrderService

# E2E 測試也使用真實的 PostgreSQL（透過 Testcontainers）
order_repo = OrderRepository(test_db_session)
product_repo = ProductRepository(test_db_session)
service = OrderService(order_repo, product_repo)
```

**關鍵**：Service 不需要知道 Repository 是連到哪個資料庫，這讓測試和生產可以無縫切換。

---

## 檔案創建順序

按照由外到內的順序創建檔案：

```
步驟 1: 創建 schemas (如果需要)
→ app/schemas/order.py
→ 定義 Request/Response 的 Pydantic models

步驟 2: 創建 services
→ app/services/order_service.py
→ 實作業務邏輯

步驟 3: 創建 API endpoints
→ app/api/orders.py
→ 定義路由和 HTTP 處理

步驟 4: 在 main.py 中註冊路由
→ app/main.py
→ 將 API router 加入 FastAPI app
```

---

## 架構檢查清單

在完成程式開發時，確保符合以下條件：

- ✅ Controllers 在 `app/api/` (如 `orders.py`, `products.py`)
- ✅ Services 在 `app/services/` (如 `order_service.py`, `inventory_service.py`)
- ✅ Repositories 在 `app/repositories/` (如 `order_repository.py`, `product_repository.py`)
- ✅ Models 在 `app/models/` (如 `order.py`, `product.py`)
- ✅ Schemas 在 `app/schemas/` (如 `order.py`, `product.py`)
- ✅ **不要**把 domain 程式碼放在 `app/walking_skeleton/`
- ✅ Service 必須支援依賴注入
- ✅ 每層只負責自己的職責

---

## 常見錯誤

### ❌ 錯誤 1：業務邏輯寫在 Controller

```python
# ❌ 錯誤
@router.post("/api/orders")
def create_order(request):
    product = db.query(Product).filter_by(id=request.product_id).first()
    if product.stock < request.quantity:  # 業務邏輯不應在 Controller
        raise HTTPException(400, "庫存不足")
    # ...
```

```python
# ✅ 正確
@router.post("/api/orders")
def create_order(request):
    service = OrderService()
    return service.create_order(...)  # 業務邏輯在 Service
```

### ❌ 錯誤 2：Service 直接操作資料庫

```python
# ❌ 錯誤
class OrderService:
    def create_order(self):
        db.query(Order).filter_by(...)  # Service 不應直接操作資料庫
```

```python
# ✅ 正確
class OrderService:
    def __init__(self, repository):
        self.repository = repository

    def create_order(self):
        self.repository.find_by_id(...)  # 透過 Repository
```

### ❌ 錯誤 3：Domain 程式碼放在 walking_skeleton

```python
# ❌ 錯誤
app/walking_skeleton/api/orders.py
app/walking_skeleton/services/order_service.py
```

```python
# ✅ 正確
app/api/orders.py
app/services/order_service.py
```

---

## 總結

遵循本架構規範可以確保：
1. **職責清晰**：每層只負責自己的事
2. **易於測試**：透過依賴注入可以輕鬆切換測試和生產環境
3. **易於維護**：檔案組織清晰，容易找到對應的程式碼
4. **符合最佳實踐**：遵循分層架構和依賴注入原則

---

# 程式碼品質規範

## 目的

提升程式碼可讀性、可維護性，減少重複和複雜度。

---

## Early Return 原則

減少巢狀，提升可讀性。

```python
# ❌ 深層巢狀
def process(data):
    if data:
        if data.is_valid():
            if data.has_permission():
                return process_data(data)
            else:
                raise PermissionError()
        else:
            raise ValueError()
    else:
        raise DataError()

# ✅ Early return
def process(data):
    if not data:
        raise DataError()
    if not data.is_valid():
        raise ValueError()
    if not data.has_permission():
        raise PermissionError()

    return process_data(data)
```

---

## 靜態屬性優化

重複使用的資料提升為類別屬性，減少記憶體消耗。

```python
# ❌ 每次調用都創建
class Service:
    def process(self, status):
        mapping = {"A": "狀態A", "B": "狀態B"}  # 每次都創建
        return mapping.get(status)

# ✅ 類別靜態屬性
class Service:
    STATUS_MAPPING = {"A": "狀態A", "B": "狀態B"}  # 只創建一次

    def process(self, status):
        return self.STATUS_MAPPING.get(status)
```

---

## 命名清晰化

變數和函式名稱應清楚表達其用途。

```python
# ❌ 不清楚的命名
def process(data):
    result = data.get("id")
    return result

# ✅ 清晰的命名
def extract_user_id_from_context(context_data):
    user_id = context_data.get("user_id")
    return user_id
```

---

## DRY 原則（Don't Repeat Yourself）

消除重複邏輯，提取共用方法。

```python
# ❌ 重複的驗證邏輯
def update_progress(...):
    subscription = self.repo.find_by_user(user_id)
    if not subscription:
        raise SubscriptionNotFoundError()
    # ...

def submit_assignment(...):
    subscription = self.repo.find_by_user(user_id)
    if not subscription:
        raise SubscriptionNotFoundError()
    # ...

# ✅ 提取共用方法
def _validate_subscription(self, user_id):
    subscription = self.journey_subscription_repo.find_by_user(user_id)
    if not subscription:
        raise SubscriptionNotFoundError()
    return subscription

def update_progress(self, user_id, ...):
    subscription = self._validate_subscription(user_id)
    # ...

def submit_assignment(self, user_id, ...):
    subscription = self._validate_subscription(user_id)
    # ...
```

---

## 檢查清單

- [ ] 使用 Early Return 減少巢狀
- [ ] 重複使用的資料提升為類別屬性
- [ ] 變數和函式名稱清晰表達用途
- [ ] 消除重複邏輯，提取共用方法

---

