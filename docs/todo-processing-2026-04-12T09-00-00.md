# 待辦事項處理紀錄

**執行時間：** 2026-04-12T09:00:00+08:00（排程自動執行）
**執行者：** TiTi Commander v2.0（CEO 角色）
**觸發方式：** 每日 09:00 心跳排程

---

## 💓 TiTi 心跳報告

**時間：** 2026-04-12 09:00
**類型：** 🟢 日常巡檢

---

## 📋 任務狀態總覽

本次巡檢 `docs/ToDoList.md` 中所有待辦事項，結果如下：

| 項目 | 所屬階段 | 程式碼狀態 | 基礎設施狀態 | 備註 |
|------|----------|-----------|-------------|------|
| LLM 防火牆配置（Llama Guard） | 階段二 | ✅ 已完成 | ⏳ 等待部署 | 需 `LLAMA_GUARD_URL` 推理服務 |
| 欄位級加密（KMS） | 階段二 | ✅ 已完成 | ⏳ 等待部署 | 需設定 `FIELD_ENCRYPTION_KEY` |
| 語意快取（Semantic Cache） | 階段三 | ✅ 已完成 | ⏳ 等待部署 | 需 Redis 基礎設施 |
| 多租戶限流（Rate Limiting） | 階段三 | ✅ 已完成 | ⏳ 等待部署 | 需 Redis 基礎設施 |
| 任務佇列隔離（Celery Queue） | 階段三 | ✅ 已完成 | ⏳ 等待部署 | 需 Redis + Celery Worker |
| 全鏈路追蹤（OpenTelemetry） | 階段四 | ✅ 已完成 | ⏳ 等待部署 | 需 OTLP Collector / Grafana Tempo |

**結論：所有程式碼層任務均已完成，目前瓶頸為外部基礎設施部署。**

---

## 📊 OKR 對齊狀態

| OKR 指標 | 相關待辦項目 | 目前狀態 |
|----------|-------------|---------|
| O1-KR1（AI 輸出品質 ≥ 95%） | LLM 防火牆 | 程式碼備妥，待部署激活 |
| O2-KR2（付費轉換率） | 任務佇列隔離 | 程式碼備妥，待 Celery 基礎設施 |
| O3-KR1（LLM 成本 ≤ 15% 營收） | 語意快取 + 限流 | 程式碼備妥，待 Redis 基礎設施 |
| O3-KR2（付費用戶月均 ≥ 4 次） | 欄位加密 + 全鏈路追蹤 | 程式碼備妥，待 KMS + OTLP 部署 |

---

## 🔍 本次巡檢詳情

### 巡檢結果

**程式碼層**：所有待辦項目均已完成，無需新增程式碼。

**Git 狀態**：
- 最新 commit：`c5795d6` — Fix extraction: prioritize exam_subject_codes over subject_name
- 工作目錄：無未提交的業務程式碼變更

### 基礎設施待辦清單（需人工操作）

以下為需要 Simon（董事會）或 DevOps 手動完成的部署步驟：

#### 1. Redis 服務（解鎖 3 個功能）
```bash
# 本地開發
docker run -d --name titi-redis -p 6379:6379 redis:7-alpine

# 生產（GCP Memorystore 或 Redis Cloud）
# 設定環境變數
export REDIS_URL="redis://your-redis-host:6379/0"
```
→ 解鎖：**語意快取** + **多租戶限流** + **任務佇列隔離**

#### 2. Celery Worker 啟動（解鎖任務佇列隔離）
```bash
# 開發環境
.venv/bin/celery -A app.worker worker --loglevel=info

# 生產環境（按佇列擴展）
.venv/bin/celery -A app.worker worker -Q paid_priority -c 4 --hostname=paid@%h
.venv/bin/celery -A app.worker worker -Q standard -c 2 --hostname=std@%h
.venv/bin/celery -A app.worker worker -Q background -c 1 --hostname=bg@%h
```

#### 3. KMS 金鑰設定（解鎖欄位加密）
```bash
# 生成 Fernet 金鑰
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 設定環境變數
export FIELD_ENCRYPTION_KEY="your-generated-key"

# 執行 Alembic migration（欄位加密 flag）
.venv/bin/python -m alembic upgrade head
```

#### 4. Llama Guard 設定（解鎖 LLM 防火牆語意層）
```bash
# 選項 A：自架（Ollama + Llama Guard）
# 選項 B：使用 Replicate / Together AI API
export LLAMA_GUARD_URL="https://your-llama-guard-endpoint.com"
export LLAMA_GUARD_API_KEY="your-api-key"
# 注意：未設定 LLAMA_GUARD_URL 時，防火牆仍以規則引擎運作（正常服務）
```

#### 5. OpenTelemetry 追蹤（解鎖全鏈路監控）
```bash
# 選項 A：Grafana Cloud（最快）
# 選項 B：自架 OTLP Collector + Grafana Tempo
export OTEL_ENABLED=true
export OTEL_EXPORTER_OTLP_ENDPOINT="https://your-otlp-endpoint"
export OTEL_SERVICE_NAME="titi-backend"
```

---

## 🔒 需要董事會決策

目前無緊急決策事項。

以下為**建議優先順序**（供 Simon 參考）：

| 優先度 | 項目 | 理由 |
|--------|------|------|
| 🔴 高 | Redis 服務部署 | 一次解鎖 3 個功能，CP 值最高 |
| 🟡 中 | KMS 金鑰設定 | 個資保護合規需求 |
| 🟡 中 | Celery Worker 啟動 | 改善付費用戶體驗 |
| 🟢 低 | OTLP / Grafana | 監控優化，非緊急 |
| 🟢 低 | Llama Guard 語意層 | 規則引擎已提供基本防護 |

---

## 📁 本次異動

```
docs/todo-processing-2026-04-12T09-00-00.md  ← 新增（本紀錄）
```

---

## ⏭️ 下次心跳

**預計時間：** 2026-04-13 09:00
**預計內容：** 若基礎設施仍未部署，維持現狀報告；若已部署，進行功能驗證紀錄。

---

*自動產出 by TiTi Commander v2.0 | CEO 角色 | 2026-04-12*
