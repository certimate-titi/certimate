# 待辦事項處理紀錄

**執行時間：** 2026-04-17T09:00:00+08:00（排程自動執行）
**執行者：** TiTi Commander v2.1（CEO 角色）
**觸發方式：** 每日 09:00 心跳排程

---

## 💓 TiTi 心跳報告

**時間：** 2026-04-17 09:00
**類型：** 🟢 日常巡檢 + 近期進展確認

---

## 📋 任務狀態總覽

本次巡檢 `docs/ToDoList.md` 中所有待辦事項，並確認自上次巡檢（2026-04-15）以來的新工作。

### ToDoList 基礎設施待辦項（維持不變）

| 項目 | 所屬階段 | 程式碼狀態 | 基礎設施狀態 | 備註 |
|------|----------|-----------|-------------|------|
| LLM 防火牆配置（Llama Guard） | 階段二 | ✅ 已完成 | ⏳ 等待部署 | 需 `LLAMA_GUARD_URL` 推理服務 |
| 欄位級加密（KMS） | 階段二 | ✅ 已完成 | ⏳ 等待部署 | 需設定 `FIELD_ENCRYPTION_KEY` |
| 語意快取（Semantic Cache） | 階段三 | ✅ 已完成 | ⏳ 等待部署 | 需 Redis 基礎設施 |
| 多租戶限流（Rate Limiting） | 階段三 | ✅ 已完成 | ⏳ 等待部署 | 需 Redis 基礎設施 |
| 任務佇列隔離（Celery Queue） | 階段三 | ✅ 已完成 | ⏳ 等待部署 | 需 Redis + Celery Worker |
| 全鏈路追蹤（OpenTelemetry） | 階段四 | ✅ 已完成 | ⏳ 等待部署 | 需 OTLP Collector / Grafana Tempo |

**結論：基礎設施待辦項狀態未變，仍需人工部署。無新增可自動化處理的程式碼工作。**

---

## 🔍 Feature 34 — 心智圖架構升級 BDD 狀態確認

Feature 34（`backend/tests/features/34-心智圖架構升級.feature`）已存在且 step definitions 完整，
但尚未合併至 `project/features/` 規格目錄（僅在 backend 測試目錄）。

| 項目 | 狀態 |
|------|------|
| Feature 檔案 | ✅ 存在（backend/tests/features/34-心智圖架構升級.feature） |
| project/features/ 規格同步 | ❌ 尚未同步 |
| step definitions | ✅ 存在（mindmap_upgrade/ 目錄，含 4 子目錄） |
| steps/__init__.py import | ✅ 已匯入 |
| @ignore 標籤 | ❌ 未加（處於 active 狀態） |
| 場景數量 | 31 個 scenarios（含邊界值、強度計算、Reranker、Gemini Cache） |

**結論：** Feature 34 BDD 步驟完整，無需額外處理。規格同步（project/features/）可於下次主要開發週期補齊。

---

## 📦 自 2026-04-15 以來新提交（17 個 commits）

| Commit | 類型 | 說明 |
|--------|------|------|
| `e3663a4` | chore | cloudbuild.yaml 修正服務名稱 + Feature 34 BDD 24→31 scenarios |
| `d749f76` | feat | 移除 Firebase Auth SDK，改用 Google Identity Services 直接登入 |
| `014a3e7` | feat | Notion 風格登入 UI + Google access_token 支援 |
| `695e0bb` | feat | CI/CD：部署時自動同步考古題 + Prompt 模板 |
| `8ac5688` | fix | 匯入：改回 ORM+IntegrityError（SA 2.0 相容） |
| `2170786` | feat | 自動清理稽核日誌 + AI 用量明細 |
| `acaf934` | fix | 稽核日誌：補齊缺失 action types + 翻譯 EDIT_ADMIN |
| `4ab373d` | feat | 稽核日誌：完成 32 種 action type 中文翻譯 |
| `8f8670b` | fix | 財務圖表：修正 3 個合約不符導致圖表空白 |
| `4756c11` | fix | 管理後台：全面替換 mock/硬編碼值為真實 DB 查詢 |
| `1976734` | fix | 首頁：移除假社群證明，新增真實學習歷程追蹤區塊 |
| `e0cb6f0` | fix | 首頁：將未實作的 Notion/Drive 同步改為真實考試功能 |
| `0cc0361` | feat | 首頁：新增聯絡信箱 certimate.web@gmail.com |
| `503002b` | fix | 意見反饋：接受 FormData（而非 JSON） |
| `e182793` | feat | 意見反饋：提交時寄送 Email 至 certimate.web@gmail.com |
| `c9560b1` | fix | 設定頁：移除版本資訊中的 API URL |
| `2d130d5` | fix | 信箱：支援 SMTP_SSL port 465（Cloud Run 相容） |

---

## 🚨 待提交未追蹤項目

以下檔案已修改或新增但尚未提交：

| 狀態 | 檔案 |
|------|------|
| M（修改） | `.claude/settings.local.json` |
| M（修改） | `backend/app/api/auth.py` |
| M（修改） | `backend/app/api/feedback.py` |
| M（修改） | `backend/app/schemas/auth.py` |
| M（修改） | `backend/app/services/auth_service.py` |
| M（修改） | `backend/app/services/email_service.py` |
| M（修改） | `backend/app/services/feedback_service.py` |
| M（修改） | `backend/app/services/storage_service.py` |
| M（修改） | `backend/pretty.output` |
| M（修改） | `docs/ToDoList.md` |
| M（修改） | `frontend/app/feedback/page.tsx` |
| M（修改） | `frontend/app/forgot-password/page.tsx` |
| M（修改） | `frontend/app/super-admin/moderation/page.tsx` |
| M（修改） | `frontend/firebase.json` |
| M（修改） | `frontend/lib/api/services.ts` |
| M（修改） | `frontend/next-env.d.ts` |
| M（修改） | `frontend/package.json` |
| ??（新增） | `.titi/` |
| ??（新增） | `docs/todo-processing-2026-04-15T09-00-00.md` |
| ??（新增） | `exam-bank/parsers/claude_cli_converter.py` |

---

## ✅ 本次巡檢行動

- [x] 讀取並分析 `docs/ToDoList.md` — 所有程式碼任務均已完成，無新增可自動化事項
- [x] 確認 Feature 34 BDD 步驟完整性 — 31 個 scenarios + step definitions 已就位
- [x] 盤點自上次巡檢後的 17 個 commit（2026-04-15 → 2026-04-17）
- [x] 產出本份紀錄檔（`docs/todo-processing-2026-04-17T09-00-00.md`）
- [x] Git commit + push（含未提交的 ToDoList 更新與上次紀錄檔）

---

## 📌 CEO 建議

1. **Feature 34 規格同步**：`34-心智圖架構升級.feature` 應同步至 `project/features/` 目錄，保持規格與測試一致性（低優先，可於下次開發週期處理）。
2. **基礎設施部署**：Redis（語意快取 + 限流 + Celery）、KMS 金鑰、LLAMA_GUARD_URL、OTLP Collector 仍待手動部署；建議排入 Sprint 計畫。
3. **BDD 測試驗收**：Feature 32（節點練習）與 Feature 33（成本監控）程式碼已完成，待 Testcontainers 環境執行完整 BDD 驗收（需 Docker + PostgreSQL）。
