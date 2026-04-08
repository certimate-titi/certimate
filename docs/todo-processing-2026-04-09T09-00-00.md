# 🤖 TiTi CEO 自動處理紀錄

**時間戳記**：2026-04-09T09:00:00  
**觸發方式**：🟢 日常心跳（排程自動執行）  
**處理人員**：CEO（Claude 自動運作）  
**董事會審核**：待確認

---

## 📋 本次處理摘要

檢查 `docs/ToDoList.md` 後，發現 **6 個待辦事項**，分布於階段二、三、四。
本次心跳針對「可透過程式碼實現」的項目進行自動推進，「需外部基礎設施」的項目補充完整的實作代碼，待基礎設施就緒即可啟用。

**目標對齊**：O3 - KR1（LLM API 成本佔營收 ≤ 15%）/ O3 - KR2（租戶安全與資料隔離）

---

## ✅ 1. 欄位級加密（階段二）

**狀態**：✅ 程式碼實作完成（待基礎設施：KMS 金鑰管理）  
**目標對齊**：O3 - KR2（租戶資料安全）

### 新增/修改檔案

| 檔案 | 說明 |
|------|------|
| `backend/app/core/field_encryption.py` | Fernet 對稱加密服務（新增）|
| `backend/app/models/answer.py` | 更新 Answer 模型，新增 `is_answer_encrypted`、`encrypted_at` 欄位，`get_plain_answer()`、`set_encrypted_answer()` 便利方法 |
| `backend/alembic/versions/041_add_answer_encryption_flag.py` | Migration 041：新增加密旗標欄位 |

### 技術決策

- 採用 **Fernet 對稱加密**（AES-128-CBC + HMAC-SHA256），每次加密含隨機 IV
- 以 `enc:` 前綴區分明文與密文，向下相容舊資料
- 支援**金鑰輪替**：`FIELD_ENCRYPTION_KEY_PREVIOUS` 環境變數讓舊密文能解密
- `selected_answer` 欄位長度由 `String(10)` 擴展至 `String(512)` 以容納 token
- 測試環境使用固定開發金鑰，正式環境必須設定 `FIELD_ENCRYPTION_KEY`

### 待手動執行

```bash
# 1. 執行 Migration
cd backend && .venv/bin/python -m alembic upgrade head

# 2. 產生正式環境金鑰
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# 將輸出設定至環境變數 FIELD_ENCRYPTION_KEY

# 3. 批次加密現有資料（正式環境部署後）
# 執行 backend/scripts/encrypt_existing_answers.py（待建立）
```

---

## ✅ 2. OpenTelemetry 全鏈路追蹤（階段四）

**狀態**：✅ 程式碼實作完成（待基礎設施：OTLP Collector / Grafana Tempo）  
**目標對齊**：O3 - KR1（LLM API 成本追蹤）

### 新增/修改檔案

| 檔案 | 說明 |
|------|------|
| `backend/app/core/telemetry.py` | OpenTelemetry 初始化 + Tenant ID Span 注入（新增）|
| `backend/app/main.py` | lifespan 中加入 `setup_telemetry(app)` 呼叫 |

### 技術決策

- `OTEL_ENABLED=false`（預設）：無 collector 時不報錯，優雅降級為 NoOp
- 支援 **OTLP gRPC exporter**（生產）與 **Console exporter**（本機 debug）
- `_request_hook`：自動將 `tenant_id` 注入每個 HTTP Span
- `record_llm_usage()`：記錄 LLM input/output tokens，追蹤 O3 KR1 成本
- **FastAPI + SQLAlchemy 自動 Instrument**（需安裝對應套件）

### 安裝依賴

```bash
pip install opentelemetry-distro \
            opentelemetry-exporter-otlp-proto-grpc \
            opentelemetry-instrumentation-fastapi \
            opentelemetry-instrumentation-sqlalchemy
```

### 啟用方式

```bash
# .env
OTEL_ENABLED=true
OTEL_SERVICE_NAME=certimate-api
OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4317  # Grafana Tempo
```

---

## ✅ 3. 多租戶限流 Redis Token Bucket（階段三）

**狀態**：✅ 程式碼實作完成（待基礎設施：Redis）  
**目標對齊**：O3 - KR2（租戶公平使用 + DDoS 防護）

### 新增/修改檔案

| 檔案 | 說明 |
|------|------|
| `backend/app/core/rate_limit.py` | Token Bucket Middleware（Redis + 記憶體 Fallback）（新增）|
| `backend/app/main.py` | 加入 `RateLimitMiddleware` |

### QPS 限制設定

| 等級 | 環境變數 | 預設 QPS | 說明 |
|------|----------|----------|------|
| B2C FREE | `B2C_FREE_QPS` | 10 req/s | 免費版 |
| B2C PRO/PRO+ | `B2C_PRO_QPS` | 30 req/s | PRO_199 / PRO_PLUS_399 |
| B2C ULTRA | `B2C_ULTRA_QPS` | 100 req/s | ULTRA_1599 |
| B2B | `B2B_QPS` | 200 req/s | EDU / INSTITUTION |
| 未認證 | `DEFAULT_QPS` | 5 req/s | IP 限流 |

### 技術決策

- **Lua Script 原子操作**：Redis `EVALSHA` 避免 Race Condition
- **JWT 解析**：從 Authorization header 取得 `tenant_id` + `plan`
- **IP Fallback**：未認證流量以 IP 計算（支援 X-Forwarded-For）
- **豁免路徑**：`/health`、`/docs`、`/redoc`、`/openapi.json`
- **回應 Headers**：`X-RateLimit-Limit`、`X-RateLimit-Remaining`、`X-RateLimit-Reset`

### 啟用方式

```bash
# .env
REDIS_URL=redis://redis:6379/0
RATE_LIMIT_ENABLED=true
```

---

## ✅ 4. 語意快取 Semantic Cache（階段三）

**狀態**：✅ 程式碼實作完成（待基礎設施：Redis）  
**目標對齊**：O3 - KR1（LLM API 成本 ≤ 15% 營收）

### 新增/修改檔案

| 檔案 | 說明 |
|------|------|
| `backend/app/services/semantic_cache_service.py` | 語意快取服務（Redis + 記憶體 Fallback）（新增）|

### 技術決策

- **快取鍵值**：`semantic:{tenant_id}:{sha256_hash[:32]}` — 每租戶隔離
- **Hash 計算**：`SHA-256(normalize(prompt))` — 大小寫/空白不敏感
- **支援 context 參數**：加入 `subject_id`、`document_id` 精確區分快取
- **租戶清除**：`invalidate_tenant(tenant_id)` 支援批次清除
- **TTL**：預設 24 小時（`SEMANTIC_CACHE_TTL` 覆蓋）
- **未來擴展**：預留向量相似度匹配接口（`SEMANTIC_SIMILARITY_THRESHOLD`）

### 整合範例

```python
from app.services.semantic_cache_service import get_semantic_cache

cache = get_semantic_cache()

async def generate_question(tenant_id: str, prompt: str, subject_id: str):
    # 查詢快取
    cached = await cache.get(tenant_id, prompt, context=subject_id)
    if cached:
        return cached  # 節省 LLM API 費用

    # 呼叫 LLM
    result = await llm_service.generate(prompt)

    # 存入快取
    await cache.set(tenant_id, prompt, result, context=subject_id)
    return result
```

---

## ⏭️ 未處理項目（需外部基礎設施或人工評估）

### 🟡 LLM 防火牆配置（階段二）

**原因**：需外部 LLM inference 服務（Llama Guard）  
**建議**：評估使用 Together.ai 或自建 Llama Guard 端點  
**後續行動**：待董事會決定 LLM 防火牆供應商後開始實作

### 🟡 Celery 任務佇列隔離（階段三）

**原因**：需 Celery + Redis broker 完整架構  
**建議**：搭配 Redis 基礎設施一起部署（已有限流 + 語意快取共用 Redis）  
**後續行動**：Redis 就緒後，新增 `backend/app/core/celery_app.py`

---

## 📊 OKR 進展評估

| 目標 | 指標 | 本次進展 | 備註 |
|------|------|----------|------|
| O3 KR1 | LLM 成本 ≤ 15% | 🟡 基礎建設中 | 語意快取 + OTel 成本追蹤就緒 |
| O3 KR2 | 租戶安全 | 🟡 基礎建設中 | 欄位加密 + 限流 middleware 就緒 |

---

## 🔒 G3 Gate Review 申請

**CEO 向董事會報告：**

本次心跳完成了 4 項程式碼實作（欄位加密、OTel 追蹤、多租戶限流、語意快取），所有模組均支援 Redis 優先 + 記憶體降級，可在無 Redis 的環境中正常運行。

**待董事會決策：**

1. **Redis 部署時程**：確認 Redis 基礎設施就緒日期（影響限流 + 語意快取上線）
2. **Alembic migration 041**：請在 Redis 就緒後手動執行 `alembic upgrade head`
3. **KMS 金鑰方案**：欄位加密需確認使用 GCP KMS / AWS KMS / 自管金鑰
4. **LLM 防火牆供應商**：Llama Guard 或其他意圖過濾方案

---

*本紀錄由 CEO（Claude）自動產生，詳細 diff 請參考 git commit log。*
