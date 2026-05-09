# 待辦事項處理紀錄 — 2026-04-10T02:05:35

## 執行摘要

本次由 **TiTi Commander（CEO + 研發工程師角色）** 自動執行日常心跳巡檢。
觸發條件：Cowork 排程任務自動呼叫。

---

## 處理項目

### ✅ 項目一：LLM 防火牆配置（階段二）

**任務描述：** 導入意圖過濾器，防止針對特定租戶題庫的 Prompt Injection 攻擊。

**🧭 目標對齊：O3 - KR1（安全防護 / LLM 成本控制）**

**實作內容：**

**新增 `backend/app/core/llm_firewall.py`**（完整實作）：

| 元件 | 說明 |
|------|------|
| `ThreatCategory` enum | Llama Guard S1–S14 標準分類 + C1–C4 自訂分類 |
| `FirewallResult` dataclass | 檢查結果（is_safe、category、confidence、latency） |
| `_rule_based_check()` | 正則表達式 rule-based fallback（零延遲、零依賴） |
| `_call_llama_guard()` | 呼叫外部 Llama Guard 推論服務（OpenAI-compatible API） |
| `LLMFirewall` 主類別 | 三層防護：rule-based → tenant blocklist → Llama Guard |
| `get_llm_firewall()` | FastAPI Depends 單例工廠函式 |

**防護層級（依序執行）：**
1. **Rule-based 快速過濾**：18 個正規表達式模式，覆蓋 Prompt Injection、系統 Prompt 洩露、跨租戶探測、考試作弊等攻擊類型
2. **租戶自訂 Blocklist**：管理員可設定每個租戶的禁止主題（題庫保護）
3. **Llama Guard 深度分析**：呼叫外部推論服務（設定 `LLAMA_GUARD_ENDPOINT` 啟用）

**優雅降級：** Llama Guard 不可用 → 自動退回 rule-based，不阻塞主要流程

**環境變數：**
- `LLM_FIREWALL_ENABLED` — 是否啟用（預設 true）
- `LLAMA_GUARD_ENDPOINT` — 外部推論服務 URL（選填；未設定時僅用 rule-based）
- `LLAMA_GUARD_API_KEY` — API 金鑰
- `LLAMA_GUARD_TIMEOUT` — 請求逾時秒數（預設 3）
- `LLAMA_GUARD_MODEL` — 模型名稱（預設 meta-llama/Llama-Guard-3-8B）

**整合 `backend/app/main.py`：** lifespan 啟動時預熱 LLM Firewall 單例

**使用方式（API 層）：**
```python
from app.core.llm_firewall import get_llm_firewall

@router.post("/generate")
async def generate(
    req: GenerateRequest,
    firewall: LLMFirewall = Depends(get_llm_firewall),
):
    result = await firewall.check(req.prompt, tenant_id=current_user.tenant_id)
    if not result.is_safe:
        raise HTTPException(400, detail=result.block_reason)
```

**待外部基礎設施：**
- 部署 Llama Guard 3 推論服務（vLLM / Ollama / Together AI / Hugging Face Inference Endpoints）
- 設定 `LLAMA_GUARD_ENDPOINT` 環境變數後即可啟用深度分析

---

### ✅ 項目二：任務佇列隔離（Queue Prioritization，階段三）

**任務描述：** 設定 Celery 優先權佇列，確保付費租戶的解析任務（OCR/STT）優先執行。

**🧭 目標對齊：O2 - KR3（NPS 淨推薦值 ≥ 40）；O3 - KR2（付費用戶月均完成次數 ≥ 4）**

**實作內容：**

**更新 `backend/app/worker.py`：**

| 佇列 | 優先級 | 適用對象 | x-max-priority |
|------|--------|----------|----------------|
| `priority_high` | 最高 | B2B、PRO_199、PRO_PLUS_399、ULTRA_1599、EDU | 10 |
| `priority_normal` | 中 | B2C FREE、一般用戶 | 5 |
| `default` | 低 | 背景任務（結算、清理、通知） | 3 |

- 使用 `kombu.Exchange` + `kombu.Queue` 定義三條佇列
- 新增 `TASK_ROUTES` 自動路由規則
- 更新 `include` 新增 `app.tasks.document_processing`

**新增 `backend/app/tasks/document_processing.py`：**

| 任務函式 | 功能 | 預設佇列 | Timeout |
|----------|------|----------|---------|
| `process_pdf_ocr` | PDF OCR 解析 | priority_normal | 120s / 180s |
| `process_audio_stt` | 語音轉文字 | priority_normal | 300s / 360s |
| `process_image_ocr` | 手寫圖片 OCR | priority_normal | 60s / 90s |
| `generate_ai_questions` | AI 考題生成 | priority_normal | 240s / 300s |
| `batch_generate_questions` | 批次大量出題 | default | 600s / 720s |

- `dispatch_document_task()` 統一派發函式：自動依 `subscription_plan` 選擇佇列
- 付費方案（PRO_199/PRO_PLUS_399/ULTRA_1599/EDU/B2B）→ `priority_high`
- `CELERY_ENABLED=false` 時退回同步執行（開發 / 測試環境）

**Worker 啟動指令（已更新 docstring）：**
```bash
# 全佇列（開發用）
celery -A app.worker worker -Q priority_high,priority_normal,default --concurrency=4

# 付費租戶專屬 Worker
celery -A app.worker worker -Q priority_high --concurrency=4 --hostname=premium@%h

# 一般用戶 Worker
celery -A app.worker worker -Q priority_normal,default --concurrency=2 --hostname=standard@%h
```

**待外部基礎設施：**
- Redis 仍需部署（同語意快取 / 限流）
- 確認 `kombu` 已在 requirements.txt（Celery 依賴，通常已隨 celery 安裝）

---

## 新增 / 修改檔案清單

| 檔案 | 動作 | 說明 |
|------|------|------|
| `backend/app/core/llm_firewall.py` | **新增** | LLM 防火牆核心模組（380 行） |
| `backend/app/tasks/document_processing.py` | **新增** | 文件處理 Celery 任務（OCR/STT/AI 生成）（220 行） |
| `backend/app/worker.py` | **修改** | 新增三條優先佇列、任務路由規則 |
| `backend/app/main.py` | **修改** | lifespan 加入 LLM Firewall 預熱 |

---

## 未完成項目（需外部基礎設施）

以下項目程式碼已完備，僅需部署外部服務後設定環境變數即可啟用：

| 項目 | 需要 | 環境變數 |
|------|------|----------|
| Llama Guard 深度分析 | Llama Guard 推論服務 | `LLAMA_GUARD_ENDPOINT` |
| Celery 優先佇列 | Redis | `CELERY_BROKER_URL`、`REDIS_URL` |
| 欄位級加密（已完成 2026-04-09） | KMS 金鑰 | `FIELD_ENCRYPTION_KEY` |
| 限流 / 語意快取（已完成 2026-04-09） | Redis | `REDIS_URL` |
| 全鏈路追蹤（已完成 2026-04-09） | OTLP Collector + Grafana Tempo | `OTEL_ENABLED=true` |

---

## CEO 回報摘要（給董事會）

本次心跳成功推進 **2 項**長期待辦：
1. LLM 防火牆：rule-based 過濾器已上線，Llama Guard 端點設定後即可啟用深度分析
2. Celery 優先佇列：完整實作三層佇列隔離，付費用戶任務優先保障

剩餘待外部基礎設施（Redis + Llama Guard + KMS）的項目已全數完成程式碼，待 Simon 核准部署即可全面啟用。

下次心跳預定：2026-04-11T09:00
