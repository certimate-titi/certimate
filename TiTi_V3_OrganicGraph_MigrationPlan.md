# TiTi V3 有機生長動態圖譜 — 從 V4 回退至 V3 改動計畫

**日期**：2026-04-09
**決策**：董事會選擇 A — 完全依 V3 實作，移除 V4 的時間衰退機制

---

## 架構差異對照

| 維度 | V4（現狀，要移除） | V3（目標） |
|------|-------------------|-----------|
| 進度欄位 | `base_mastery` + `ease_factor` + `retention` | `progress_percentage` (0.0~1.0) |
| 衰退機制 | SM-2 指數衰退 | ❌ 無衰退 |
| 練習影響 | 不寫 DB | ✅ 即時更新 progress |
| 聚合方式 | 客戶端 Web Worker | 後端批次重算 + 前端樂觀更新 |
| 考綱變更 | 軟合併 | 軟合併 + 進度稀釋 + Toast |
| 併發控制 | 無 | 樂觀鎖 (version) + Celery Fan-out |
| 狀態機 | SM-2 process_answer | 簡單加權更新 |

---

## 需要移除的檔案/程式碼

### 後端
1. **刪除** `app/services/sm2_engine.py` — SM-2 引擎
2. **修改** `app/tasks/exam_settlement.py` — 移除 SM-2 呼叫，改用簡單 progress 更新
3. **修改** `app/api/exam.py` submit endpoint — 移除 SM-2 結算
4. **修改** `app/api/refresh_quiz.py` — 移除 SM-2 refresh quiz，改為直接 progress 更新
5. **修改** `app/services/knowledge_nav_service.py` — 移除 decay 計算，改用 progress_percentage
6. **修改** `app/models/node_mastery.py` — 移除 V4 欄位備註中的 decay 說明

### 前端
7. **修改** `components/MindMapTree.tsx` — 移除 decay_status/retention 欄位，改用 progress_percentage
8. **刪除** `components/ExamSettlementScreen.tsx` — V4 結算動畫（V3 不需要全螢幕動畫）
9. **修改** `components/RefreshQuizModal.tsx` — 簡化為純 progress 更新
10. **修改** `app/dashboard/page.tsx` — 移除 decay 提醒卡
11. **保留** `public/workers/progress-aggregator.js` — V3 也需要聚合（但改為後端觸發）
12. **保留** `hooks/use-progress-worker.ts` — 前端樂觀更新仍需要

---

## 需要新增的功能

### 後端
1. **新增** `app/services/organic_progress.py` — V3 進度更新引擎
   - `update_progress(user_id, topic_id, is_correct)` — 答題後更新 progress
   - `recalculate_tree(user_id, root_topic_id)` — 遞迴重算父節點
   - `dilute_progress(user_id, root_topic_id, new_topics)` — 進度稀釋

2. **新增** `app/tasks/topology_change.py` — 考綱變更 Fan-out 任務
   - `batch_recalculate_progress(user_ids_chunk, root_topic_id)` — 批次重算
   - Celery Fan-out: Master Task → 500 人/chunk → Sub-Task

3. **修改** `app/api/practice.py` — practice submit **寫入 DB**（V3 核心差異）
4. **新增** `GET /api/v1/sync-hash` — 前端重連校準 endpoint

### 前端
5. **新增** Zustand store: `stores/progress-store.ts` — 樂觀更新 + undo
6. **新增** `PROGRESS_DILUTED` WebSocket 事件監聽 + Toast
7. **修改** 心智圖視覺化 — 純 progress_percentage 驅動顏色（無 decay）

---

## Migration 043

```sql
-- V3 改動：
-- 1. node_mastery 新增 version 欄位（樂觀鎖）
ALTER TABLE node_mastery ADD COLUMN IF NOT EXISTS version INT DEFAULT 1;

-- 2. 將 base_mastery 值回寫到 mastery_rate（保持一致）
UPDATE node_mastery SET mastery_rate = ROUND(base_mastery * 100, 2)
WHERE base_mastery > 0;

-- 注意：保留 base_mastery/ease_factor 等 V4 欄位，不刪除
-- （避免資料遺失，未來可能重啟 V4）
```

---

## 執行步驟（下一個 Session）

### Step 1: 後端引擎切換（1.5 天）
1. 建立 `organic_progress.py`（替代 sm2_engine.py）
2. 修改 practice API — 寫入 DB
3. 修改 exam settlement — 改用簡單 progress 更新
4. 建立 topology_change 任務（Celery Fan-out）
5. 修改 knowledge_nav_service — 移除 decay，改用 progress_percentage

### Step 2: 前端切換（1.5 天）
1. MindMapTree 改用 progress_percentage
2. 移除 ExamSettlementScreen
3. 加入 Zustand 樂觀更新
4. 加入 PROGRESS_DILUTED Toast
5. Dashboard 移除 decay 提醒

### Step 3: 測試（1 天）
1. BDD Feature 04 驗證
2. 練習即時更新驗證
3. 進度稀釋驗證

### Step 4: Migration 043 + 驗收（1 天）
1. 執行 migration
2. 前端 build 驗證
3. 完整流程 E2E

---

## 指令摘要

下一個 session 開始時執行：
```
/titi-commander 執行 V3 有機生長圖譜改動，參考 TiTi_V3_OrganicGraph_MigrationPlan.md
```

---

*文件位置*：`project/TiTi_V3_OrganicGraph_MigrationPlan.md`
*狀態*：🔒 G1 已批准（選項 A），待執行
