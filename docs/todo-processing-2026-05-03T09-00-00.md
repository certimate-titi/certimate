# TiTi Commander 排程巡檢處理紀錄

**時間**：2026-05-03  
**觸發方式**：排程自動巡檢（check-todo）  
**處理角色**：TiTi Commander（CEO + 前端工程師）

---

## 待辦項目掃描結果

掃描 `docs/ToDoList.md`，識別出 18 項未解決待辦（🔴3 🟠10 🟡5）。  
本次聚焦可立即修復的 **3 項程式碼級 BUG**（P1 × 1、P2 × 1、Feature 缺失 × 1）。

---

## 修復項目

### 1. ✅ [P1 BUG] PRO_PLUS_399 題數上限錯誤

**問題**：`TIER_QUESTION_LIMITS` 中 `PRO_PLUS_399.max` 設為 `50`，但 Feature 04 L71-83 明確規定 PRO_PLUS 上限為 **100 題**。

**修復檔案**：`frontend/app/exam/setup/page.tsx` L31

**修改內容**：
```diff
- PRO_PLUS_399: { max: 50, upgradeMessage: 'PRO 方案每次測驗最多 50 題，升級 ULTRA 最多可出 100 題以上' },
+ PRO_PLUS_399: { max: 100, upgradeMessage: 'PRO_PLUS 方案每次測驗最多 100 題，升級 ULTRA 無題數上限' },
```

**驗證**：Feature 04 L71 `PRO_PLUS 方案每次測驗題數上限為 100 題` ✅

---

### 2. ✅ [P2 BUG] PRO_199 升級提示文字錯誤

**問題**：PRO_199 的 `upgradeMessage` 為「升級 ULTRA 最多可出 100 題以上」，但 Feature 04 L65 規格為「升級 PRO_PLUS 最多可出 100 題」。PRO_PLUS_399 也沿用相同錯誤文字。

**修復檔案**：`frontend/app/exam/setup/page.tsx` L30-31

**修改內容**：
```diff
- PRO_199: { max: 50, upgradeMessage: 'PRO 方案每次測驗最多 50 題，升級 ULTRA 最多可出 100 題以上' },
+ PRO_199: { max: 50, upgradeMessage: 'PRO 方案每次測驗最多 50 題，升級 PRO_PLUS 最多可出 100 題' },
```

**驗證**：Feature 04 L65 `升級 PRO_PLUS 最多可出 100 題` ✅

---

### 3. ✅ [Feature 缺失] 結果頁交錯練習標籤

**問題**：Feature 19 L85-89 規格要求結果頁顯示排列模式標籤「交錯練習」及提示文字，但頁面無任何 `question_order_mode` 顯示邏輯。

**修復檔案**（3 處）：

1. **`frontend/types/models.ts`** — Exam interface 新增 `questionOrderMode?: string`
2. **`frontend/lib/api/services.ts`** L280 — getResults 映射新增 `questionOrderMode: raw.question_order_mode`
3. **`frontend/app/exam/results/page.tsx`** L132-139 — 新增交錯練習標籤 UI：
   - 🔀 交錯練習 badge（indigo 配色，pill 形狀）
   - 提示文字：「交錯練習有助於長期記憶，持續使用效果更佳」
   - 僅當 `exam.questionOrderMode === 'interleaved'` 時顯示

**驗證**：
- 後端 `Exam.question_order_mode` 欄位已存在（`backend/app/models/exam.py` L77）
- DBML `erm.dbml` L488 已定義該欄位
- Feature 19 L88-89 規格對齊 ✅

---

## 編譯驗證

```bash
cd frontend && npx tsc --noEmit
# 結果：零錯誤 ✅
```

---

## 剩餘未解決項目（15 項）

### 🔴 Feature 缺失（3 項）
1. `/dashboard` — StudyBuddyBanner（ULTRA 共讀橫幅）無 Feature 覆蓋
2. `/exam/workspace` — Feature 05 AI 打氣語句 UI 未實作
3. `/knowledge/mindmap` — 節點點擊互動行為無 Feature Scenario
4. `/exam/results` — Feature 06 LinkedIn 分享規格與實作不同步
5. `/account` — 通知偏好 localStorage vs API 不同步

### 🟠 實作缺失（7 項）
1. `/super-admin/anomaly` — Feature 16 批次修復缺 UI
2. `/knowledge` — 新增資源按鈕導向錯誤
3. `/exam/workspace` — Feature 20 信心度校準 UI 缺失
4. `/practice` — Feature 20 信心度校準 UI 缺失
5. `/exam/setup` — ULTRA Bloom 比例 isAdmin vs isUltra 守衛錯誤
6. `/exam/setup` — SSE 推送 vs 假動畫
7. `/account` — 通知偏好需改為後端 API

### 🟡 空態補強（5 項）
1. `/practice` — no-questions 未查 resource_parse_jobs
2. `/review` — wrongQuestions 空態未查 job 表
3. `/schedule` — recs 空態未查 job 表
4. `/account/weekly-reports` — reports 空態未查 job 表
5. `/knowledge/mindmap` — mindMapNodes 空態未查 resource_parse_jobs
6. `/knowledge` — documents+nodes 空態未查 resource_parse_jobs

---

## 下次巡檢建議優先處理

1. **P1**: `/exam/setup` — ULTRA Bloom 比例 `isAdmin` → `isUltra` 守衛修正（直接影響付費用戶）
2. **P2**: `/exam/workspace` + `/practice` — Feature 20 信心度校準 😰😐😎 UI 實作
3. **P2**: 空態補強批次處理（6 項 Layer 3 違規）
