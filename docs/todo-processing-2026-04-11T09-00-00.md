# 待辦事項處理紀錄

**執行時間：** 2026-04-11T09:00:00+08:00（排程自動執行）
**執行者：** TiTi Commander v2.0（CEO 角色）
**觸發方式：** 每日 09:00 心跳排程

---

## 📋 任務摘要

本次處理 `docs/ToDoList.md` 中剩餘的 2 個未完成 `[ ]` 項目：

| 項目 | 所屬階段 | 狀態 |
|------|----------|------|
| LLM 防火牆配置（Llama Guard 意圖過濾器） | 階段二 | ✅ 程式碼完成 |
| 任務佇列隔離（Celery 優先權佇列） | 階段三 | ✅ 程式碼完成 |

---

## 🔒 任務一：LLM 防火牆配置

### 背景

防止針對特定租戶題庫的 Prompt Injection 攻擊。原本標記為「需外部 LLM inference 服務」，
故僅規劃未實作。本次以「程式碼先行、基礎設施後接」策略完成程式碼層。

### 實作內容

**新增檔案：** `backend/app/core/llm_firewall.py`

#### 架構設計

雙層防護機制：

**Layer 1 — 規則引擎（_RuleEngine）**
- 同步執行，零外部依賴，零額外延遲
- 覆蓋 4 類威脅，共 17 條正則表達式規則：
  - Prompt Injection（忽略指令型、系統提示詞萃取型、代碼注入型）
  - Jailbreak（DAN 模式、無限制模式、中英文混合）
  - 跨租戶資料存取（題庫萃取、多語言）
  - PII 萃取（學生姓名、信箱、密碼）
- 長度防護：超過 50,000 字元自動阻擋

**Layer 2 — Llama Guard 客戶端（_LlamaGuardClient）**
- 對接外部 Llama Guard 推理服務（`meta-llama/Llama-Guard-3-8B`）
- 熔斷器機制：失敗後 60 秒不重試，自動恢復
- 優雅降級：Llama Guard 不可用時僅使用規則引擎
- 分類對應：S1→PROMPT_INJECTION / S2→JAILBREAK / S3→CROSS_TENANT / S4→PII_EXTRACTION

**主類別 LLMFirewall**
- `check_sync()`：同步版本（Celery task 使用）
- `check()`：非同步版本（FastAPI route 使用），偵測到威脅時拋出 `PromptInjectionError`
- OTel span 記錄所有威脅事件
- `log_only` 模式：僅記錄不阻擋（灰度發布用）

#### 環境變數

| 變數 | 預設 | 說明 |
|------|------|------|
| `LLM_FIREWALL_ENABLED` | `true` | 是否啟用 |
| `LLAMA_GUARD_URL` | 空（不啟用） | Llama Guard 推理端點 |
| `LLAMA_GUARD_API_KEY` | 空 | API 金鑰 |
| `LLAMA_GUARD_TIMEOUT` | `3` | 請求逾時秒數 |
| `LLM_FIREWALL_LOG_ONLY` | `false` | 僅記錄不阻擋 |

#### main.py 整合

```python
from app.core.llm_firewall import PromptInjectionError, prompt_injection_exception_handler
app.add_exception_handler(PromptInjectionError, prompt_injection_exception_handler)
```

#### 使用方式（路由層）

```python
from app.core.llm_firewall import get_llm_firewall, LLMFirewall
from fastapi import Depends

@router.post("/ai/ask")
async def ask_ai(
    body: AskRequest,
    firewall: LLMFirewall = Depends(get_llm_firewall),
    current_user: User = Depends(get_current_user),
):
    await firewall.check(body.prompt, tenant_id=str(current_user.tenant_id))
    # ... 正常業務邏輯
```

### 待手動執行

```bash
# 設定 Llama Guard 推理服務（部署就緒後）
export LLAMA_GUARD_URL="https://your-llama-guard-endpoint.com"
export LLAMA_GUARD_API_KEY="your-api-key"

# 測試（規則引擎，無需外部服務）
curl -X POST http://localhost:8000/api/v1/ai/ask \
  -H "Authorization: Bearer {token}" \
  -d '{"prompt": "ignore all previous instructions and..."}'
# 預期：HTTP 400 {"detail": "輸入內容含有不允許的指令模式", "code": "PROMPT_INJECTION"}
```

---

## 🚀 任務二：任務佇列隔離（Celery 優先權佇列）

### 背景

確保付費租戶（B2B + ULTRA_1599）的文件解析任務（OCR/STT）優先於免費用戶執行，
防止大量免費用戶上傳造成付費用戶等待。

### 實作內容

**修改檔案：** `backend/app/worker.py`
**新增檔案：** `backend/app/tasks/document_processing.py`
**修改檔案：** `backend/app/tasks/__init__.py`

#### 佇列架構

```
Redis Broker
    ├── paid_priority (x-max-priority: 9)  ← B2B + ULTRA_1599
    ├── standard      (x-max-priority: 5)  ← PRO_199 / PRO_PLUS_399
    ├── background    (x-max-priority: 1)  ← FREE
    └── celery        (x-max-priority: 5)  ← exam_settlement / topology_change
```

#### 訂閱方案 → 佇列映射

| 訂閱方案 | 佇列 | 優先度 |
|----------|------|--------|
| EDU / INSTITUTION | paid_priority | 最高 |
| ULTRA_1599 | paid_priority | 最高 |
| PRO_199 / PRO_PLUS_399 | standard | 中 |
| FREE | background | 低 |

#### 任務類型

| 任務 | 說明 |
|------|------|
| `parse_document_task` | 完整文件解析 Pipeline（OCR + 結構分析 + Embedding） |
| `ocr_image_task` | 單圖片 OCR（手寫圖片） |
| `transcribe_audio_task` | 音訊轉文字 STT（YouTube） |

#### Dispatch Helper 用法

```python
from app.tasks.document_processing import dispatch_document_parse

# 自動依方案選擇佇列
task_id = dispatch_document_parse(
    resource_id=str(resource.id),
    tenant_id=str(resource.tenant_id),
    user_plan=current_user.plan,  # "PRO_199" → standard 佇列
)
```

#### Worker 啟動命令

```bash
# 開發環境：全佇列單 Worker
.venv/bin/celery -A app.worker worker --loglevel=info

# 生產環境：各佇列獨立水平擴展
.venv/bin/celery -A app.worker worker -Q paid_priority -c 4 --hostname=paid@%h
.venv/bin/celery -A app.worker worker -Q standard -c 2 --hostname=std@%h
.venv/bin/celery -A app.worker worker -Q background -c 1 --hostname=bg@%h
.venv/bin/celery -A app.worker worker -Q celery -c 2 --hostname=default@%h
```

### 待手動執行

```bash
# 確認 Redis 運行中
docker run -d --name certimate-redis -p 6379:6379 redis:7-alpine

# 安裝 kombu（若未安裝）
.venv/bin/pip install celery[redis] kombu

# 啟動 Worker
.venv/bin/celery -A app.worker worker --loglevel=info
```

---

## 📊 目標對齊

| 任務 | OKR 對齊 |
|------|----------|
| LLM 防火牆 | O3-KR1（成本控制）+ O1-KR1（AI 輸出品質） |
| 任務佇列隔離 | O2-KR2（付費轉換率）+ O3-KR2（付費用戶完成次數） |

**說明：**
- 防火牆確保 AI 輸出不被惡意指令干擾，維護題庫品質（O1）並避免異常 API 消耗（O3）
- 佇列隔離提升付費用戶體驗，降低流失率，間接提升付費轉換率（O2）

---

## 📁 異動檔案清單

```
backend/app/core/llm_firewall.py          ← 新增（LLM 防火牆）
backend/app/worker.py                     ← 更新（優先權佇列配置）
backend/app/tasks/document_processing.py  ← 新增（文件解析任務）
backend/app/tasks/__init__.py             ← 更新（新增模組 import）
backend/app/main.py                       ← 更新（防火牆例外處理器）
docs/ToDoList.md                          ← 更新（標記完成）
docs/todo-processing-2026-04-11T09-00-00.md ← 新增（本紀錄）
```

---

*自動產出 by TiTi Commander v2.0 | CEO 角色 | 2026-04-11*
