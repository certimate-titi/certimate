# PostHog 埋點規格 — 議題 C

日期：2026-05-08
作者：TiTi PM（議題 C 核准版）
目標讀者：CTO（排 ticket 用）

---

## 1. 核心事件清單（共 14 個）

| # | event name | 觸發點（前端路由 + 條件） | 必帶屬性 |
|---|-----------|--------------------------|---------|
| 1 | `user_signed_up` | `/onboarding` 初次載入（Firebase SSO 完成後） | `user_id`, `plan`, `auth_provider` |
| 2 | `onboarding_subject_selected` | `/onboarding` 科目勾選 onChange | `user_id`, `plan`, `subject_id`, `subject_count` |
| 3 | `onboarding_exam_date_set` | `/onboarding` 考期欄位 onBlur | `user_id`, `plan`, `days_until_exam` |
| 4 | `onboarding_completed` | `/onboarding` 點擊「完成」且 API 回 200 | `user_id`, `plan`, `subject_ids[]`, `days_until_exam` |
| 5 | `resource_uploaded` | `/resources` 上傳成功（parse job 建立） | `user_id`, `plan`, `subject_id`, `file_type`, `is_first_upload` |
| 6 | `quiz_started` | `/quiz/[sessionId]` 載入時 | `user_id`, `plan`, `subject_id`, `question_count`, `is_first_quiz` |
| 7 | `quiz_completed` | 最後一題提交、看到結果頁 | `user_id`, `plan`, `subject_id`, `score_pct`, `duration_sec` |
| 8 | `knowledge_map_viewed` | `/knowledge` 頁面掛載 | `user_id`, `plan`, `subject_id` |
| 9 | `confidence_trend_clicked` | `/knowledge` 信心度趨勢圖點擊展開 | `user_id`, `plan`, `subject_id` |
| 10 | `today_review_started` | `/today` 點擊「開始複習」按鈕 | `user_id`, `plan`, `due_count` |
| 11 | `today_review_completed` | `/today` 完成全部 due 卡片 | `user_id`, `plan`, `cards_reviewed`, `duration_sec` |
| 12 | `paywall_shown` | 任意頁 quota 超限觸發 paywall modal | `user_id`, `plan`, `trigger_feature`, `quota_type` |
| 13 | `pricing_page_viewed` | `/pricing` 頁面掛載 | `user_id`, `plan`, `referrer` |
| 14 | `subscription_completed` | ECPay 回調成功、plan 升級寫入後跳轉 | `user_id`, `new_plan`, `old_plan`, `amount_ntd` |

備註：`is_first_upload` / `is_first_quiz` 由前端在呼叫 API 前查 localStorage flag 判斷，首次設旗後即清除「首次」語意；不依賴後端欄位以減少耦合。

---

## 2. 三個關鍵 Funnel

### 2-A  Onboarding Funnel（取得 → 激活）

```
user_signed_up
  → onboarding_completed
    → resource_uploaded (is_first_upload = true)
      → quiz_started (is_first_quiz = true)
```

關鍵斷點：`onboarding_completed → resource_uploaded` 的流失率，反映「上傳門檻」是否過高。目標：7 日內完成率 ≥ 60%。

### 2-B  Activation Funnel（功能黏著）

```
quiz_completed (is_first_quiz = true)
  → knowledge_map_viewed
    → confidence_trend_clicked
      → today_review_started
```

關鍵斷點：`knowledge_map_viewed → confidence_trend_clicked` 的點擊率，驗證 Sprint 7-8 信心度趨勢功能是否被發現。目標：首周 ≥ 30%。

### 2-C  Conversion Funnel（免費轉付費）

```
paywall_shown
  → pricing_page_viewed
    → subscription_completed
```

關鍵斷點：`paywall_shown → pricing_page_viewed` 的到達率。`referrer` 屬性記錄從哪個 trigger_feature 流入，協助調整 paywall 文案優先度。

---

## 3. 五個 Retention 指標定義

| 指標 | 定義 | 計算方式（PostHog Insights） |
|------|------|------------------------------|
| D1 / D7 / D30 留存 | 首次 `user_signed_up` 後，第 1/7/30 天仍有任一事件的用戶比率 | Retention insight，以 `user_signed_up` 為起點事件 |
| WAU / MAU | 7/30 天內有任一事件的不重複 `user_id` 數 | Trends insight，distinct count by `user_id` |
| 訂閱轉換率 | `subscription_completed` 去重用戶 / `user_signed_up` 去重用戶（同期間） | Funnel 或 Formula insight |
| 平均訂閱壽命 | 訂閱開始到降回 FREE（或 `subscription_completed` 後的 churn event，待 Sprint 9 補建） | 暫以 PostHog Group Analytics 或後端計算；Sprint 9 補 `subscription_cancelled` 事件 |
| Sprint 7-8 功能參與率 | (a) 信心度趨勢點擊率 = `confidence_trend_clicked` / `knowledge_map_viewed`；(b) SM-2 review 完成率 = `today_review_completed` / `today_review_started` | Trends insight，Filter by date range |

---

## 4. PII 注意事項（對應 PDPA）

**絕對不能傳入 PostHog 的欄位：**

- 用戶 email、顯示姓名、電話
- 上傳檔案的原始檔名（可能含考生姓名）
- 上傳檔案內容（resource chunk text）
- Firebase UID 原值（若有關聯真實個人資料）

**處理原則：**

1. `user_id` 屬性一律使用後端內部 UUID（非 Firebase UID、非 email），PostHog 的 `distinct_id` 對應同一 UUID。
2. 前端 SDK 初始化時設定 `person_profiles: 'identified_only'`，避免匿名 session 自動建個人檔。
3. 禁止在任何 PostHog 事件的 properties 帶入自由文字欄位（如 `note`、`filename`、`raw_text`）。
4. PostHog EU Cloud（數據落點在歐洲）比 US 對 PDPA 更友好；建議 CTO 在 PostHog 建專案時選 EU region，並在隱私政策補充「行為分析」說明（議題 D 負責）。
5. 超量刪除請求：若用戶行使個資刪除權，PostHog 支援 `delete person` API；後端需有對應 `user_id` → PostHog `distinct_id` 的 mapping，建議存入現有 `users` 表的 `posthog_distinct_id` 欄位（CTO 加欄）。

---

## 5. CTO 工作量粗估

### 前端（Next.js 15）

| 工項 | 說明 | 估時 |
|------|------|------|
| 安裝 `posthog-js` + Provider 包裹 | `app/layout.tsx` 加 `PostHogProvider`，讀 env `NEXT_PUBLIC_POSTHOG_KEY` | 0.5 天 |
| 識別用戶 | `posthog.identify(user_uuid)` 在 JWT decode 後呼叫 | 0.5 天 |
| 逐頁 fire 14 個事件 | 集中在 `useEffect` / onClick handler；`is_first_*` 用 localStorage flag | 2 天 |
| Paywall modal 事件 | `paywall_shown` 在 modal 開啟時 fire，需確認各 quota guard 位置 | 0.5 天 |

前端小計：約 3.5 天

### 後端（FastAPI）

| 工項 | 說明 | 估時 |
|------|------|------|
| `users` 表加 `posthog_distinct_id` 欄位 | Alembic migration，存 UUID | 0.5 天 |
| `subscription_completed` server-side fire（可選） | ECPay 回調在後端確認付款後，以 PostHog Python SDK fire，確保不被前端 ad-blocker 漏掉 | 1 天 |
| 刪除 API（PDPA 合規） | `DELETE /api/v1/users/me` 時同步呼叫 PostHog delete person API | 0.5 天 |

後端小計：約 2 天（若 `subscription_completed` 只走前端則 1 天）

**總估時：約 5.5 天（純前端方案 4.5 天）**

---

## 範圍邊界

- **In scope**：14 個事件定義、三個 funnel、五個 retention 指標、PostHog JS SDK 整合
- **Out of scope**：A/B Test（PostHog Experiments）、後端 events table（不建，全走 PostHog Cloud）、自建 BI dashboard（PostHog Insights 即可）、`subscription_cancelled` event（Sprint 9 補）

## 依賴與風險

- PostHog free tier 上限 100k events/month；MAU < 1000 且 14 個事件下，日均事件上限約 3,333，足夠。若 MAU 破 2000 需評估升方案（$0 → $20/month）。
- ECPay 回調在後端，`subscription_completed` 若只走前端有被 ad-blocker 漏掉的風險；建議後端補 server-side fire。
- PDPA 隱私政策更新為議題 D 負責，本議題不包含法律文件修改。
