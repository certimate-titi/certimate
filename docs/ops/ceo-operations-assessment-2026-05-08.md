# CEO 運營評估啟動 — 2026-05-08

> **背景**：CTO 線 Sprint 7+8 收斂中（PR #14/#15/#16 落地），CEO 線啟動運營評估。本文是首輪盤點，列 5 個關鍵商業議題與董事會（Simon）需簽核的決策清單，避免空泛 PPT。
> **方法**：每議題附「現狀 → 風險/機會 → 選項 → 推薦」。
> **後續**：每個議題若批准展開，才召喚對應 L2 角色（產品 / 財務 / 營銷 / 法務 / 客戶成功）做深掘。

---

## 議題 A：訂閱配額 vs 實際使用 — 哪個 tier 該調整？

### 現狀（[backend/app/services/subscription_service.py:39-43](backend/app/services/subscription_service.py:39)）

| Plan | 月費 (NTD) | daily_chat | monthly_upload | monthly_exam | vision_pages | advanced_coach |
|------|-----------:|-----------:|---------------:|-------------:|-------------:|:--------------:|
| FREE | 0 | 3 | 5 | 10 | 0 | ❌ |
| PRO_199 | 199 | 30 | 50 | 100 | 0 | ❌ |
| PRO_PLUS_399 | 399 | 200 | 200 | 500 | 50 | ✅ |
| ULTRA_1599 | 1,599 | unlimited | unlimited | unlimited | 500 | ✅ |
| EDU | (B2B) | 5 | 0 | unlimited | 0 | ❌ |

### 風險 / 機會

- **FREE 太鬆 → 體驗夠用、不轉換**：3 chat + 5 upload 對短期備考用戶可能「夠了」，付費誘因弱
- **PRO_199 → PRO_PLUS_399 跳 4x 上限 + advanced_coach + vision，但只貴 2x**：相對 PRO_PLUS 太划算，會自我蠶食 PRO_199
- **ULTRA_1599 unlimited 風險**：1 個誤用戶可燒掉 50+ 個 PRO_PLUS 的 LLM 成本（無 hard cap）
- **vision_pages 50 頁太少**：一份 PDF 講義常 80-150 頁，PRO_PLUS 只能解析半本書

### 選項

- **A1**：FREE 砍至 1 chat + 1 upload，逼轉換（風險：流失試用者，損害口碑）
- **A2**：保留 FREE、把 PRO_199 上探至 60 chat + 80 upload；PRO_PLUS_399 vision 提升至 200 頁；ULTRA 加 fair-use cap（每月 token 上限）
- **A3**：不動價格，加裝點轉換漏斗、量化 FREE 用完配額後的轉換率，再依數據調整

### 推薦

**A3 → 數據驅動再動**。當前無量化指標支持配額調整。先做議題 C（埋點）+ 議題 B（單用戶成本）兩月後再回頭。

**需董事會簽核**：暫不動價格 / 配額。

---

## 議題 B：單用戶月成本 vs 訂閱毛利率

### 現狀

- `cost_monitor_service.py` 已接 GCP Billing Export（Cloud Run / GCS / Cloud SQL 數字可拿）
- **但缺 LLM API 成本對人頭攤提**：Voyage embedding / Gemini parse / Anthropic chat 都走 SaaS 計費，不在 GCP billing
- 既有 `ai_usage_ledger` 表記錄每次 AI 呼叫的 token 量，但**沒接成「每月毛利報表」**

### 估算（粗算，待財務角色驗）

| 元件 | FREE 月用量 | PRO_199 月用量 | 單元成本 | FREE 月成本 | PRO 月成本 |
|------|------------:|---------------:|---------:|------------:|-----------:|
| Cloud Run 流量 | 1 GB | 5 GB | $0.40/GB | $0.40 | $2.00 |
| GCS 儲存 | 100 MB | 1 GB | $0.026/GB | $0.003 | $0.026 |
| Voyage embedding | 100 doc | 500 doc | $0.0001/doc | $0.01 | $0.05 |
| Gemini parse | 5 PDF | 50 PDF | $0.05/PDF | $0.25 | $2.50 |
| Anthropic chat | 3 chat | 30 chat | $0.02/chat | $0.06 | $0.60 |
| Cloud SQL 攤提 | - | - | ~$0.30/MAU | $0.30 | $0.30 |
| **合計** | | | | **~$1.0** | **~$5.5** |

換 NTD：
- FREE：~ NTD 32/月（廣告補貼 / 引流成本）
- PRO_199：~ NTD 175 → **毛利率僅 12%**（NTD 24/月）

### 風險

- **PRO_199 毛利率太薄**：1% 重度用戶（每月用滿配額）可能直接虧損
- ULTRA_1599 沒 cap → 異常用戶單月燒 NTD 3,000+ token 無感
- **Voyage rerank（Sprint 6 T49）+ embed 持久化（T54）省的成本沒量化**：理論上 cost-per-query 降 70%（~$0.0001 → ~$0.00003），但無 dashboard 看

### 選項

- **B1**：本月內 sprint —— 「成本 → 毛利」對照儀表板（接 ai_usage_ledger × plan × user → 月毛利）
- **B2**：ULTRA 加 fair-use cap：每月 token 1.5M（~ NTD 600 LLM 成本）超過軟性提醒、3M hard stop
- **B3**：T54 embedding 持久化的省錢量化 — 跑兩週數據看真實 cost reduction

### 推薦

**B1 + B2 同 sprint 做**。B1 給未來決策依據，B2 立刻防爆。B3 自動會在 B1 dashboard 上呈現。

**需董事會簽核**：
1. 接 `ai_usage_ledger × plan` 毛利儀表板（CTO 線實作 + 財務 owner 看數）— **批准 → 召喚財務 + 後端**
2. ULTRA_1599 加 fair-use cap 文案（「異常使用提醒」+ hard stop 3M token/月）— **批准 → 召喚法務（ToS 改）+ 產品（公告流程）**

---

## 議題 C：Onboarding / Activation 漏斗 — 沒埋點等於瞎開

### 現狀

- `/onboarding` → `/dashboard` → 第一次上傳 → 第一次測驗 → D1 / D7 / D30 留存
- **完全無事件追蹤**：不知道
  - 註冊後多少 % 進入 /dashboard
  - /dashboard 進入後多少 % 上傳第一份資源
  - 第一次測驗 → D7 留存率
  - 訂閱付費點擊 → 付費完成 funnel

### 風險

- **CTO 已蓋好/today + SM-2 due + 信心度趨勢**（Sprint 7-8）這三大留存功能，但沒人量化效果 → 投入 2 sprint 卻不知道 ROI
- 行銷投放預算進來會盲開（沒 attribution）

### 選項

- **C1**：自建事件 log（route to backend `events` table + admin dashboard），1 sprint 工作量
- **C2**：接 PostHog（self-hosted 或 cloud free tier 100k events/month），1 週工作量
- **C3**：先打 5 個關鍵事件硬編碼 log（signup / first_upload / first_exam / first_review / paid），用 SQL 拉

### 推薦

**C2 PostHog cloud free tier**。100k events/月對早期用戶量足夠（MAU < 1000 級），免維運，後續可 export 自建。

**需董事會簽核**：批准 PostHog 自由帳號（無 $ 成本）+ CTO 線 1 週 sprint 接 SDK。

---

## 議題 D：AI 生成內容法務 — 最小最緊風險清單

### 現狀

- 用戶上傳 PDF 給 Gemini 解析 → 抽出題目、鷹架、知識節點
- 用戶答錯題 → AI 教練給回饋（可能含 LLM hallucination）
- YouTube 講座連結解析 → fair use 灰色地帶
- 用戶條款是否含 AI 生成內容免責？**未稽核**
- PDPA：用戶上傳的 PDF 是否做 PII 清洗 / 保留期 / 刪除權？**未稽核**

### 風險（按嚴重度）

1. **AI 給錯資訊導致用戶考試失敗** → 訴訟風險（中等，台灣判例少但有）
2. **YouTube 著作權方主張侵權**（特別是付費課程影片）→ 中等
3. **用戶 PDF 含 PII 留在 GCS / pgvector** → PDPA 罰鍰風險（高 — 台灣 PDPA 罰款最高 NTD 10M）
4. **Free / EDU tier 學生資料給 LLM 做 fine-tune** → 教育機構合約禁止條款（高 — B2B 簽約死線）

### 推薦

**先建「最小法務最緊清單」（1 週內）**：
- D1：ToS 加 AI 生成內容免責條款 + 保留 90 天後刪除政策（法務）
- D2：上傳 PDF 流程加「我同意內容供 AI 解析」勾選（前端）
- D3：YouTube 解析顯示「僅學習用、勿散播」聲明（前端）
- D4：B2B / EDU tier 額外 DPA 模板（已實作 EDU console 簽 DPA，但模板需法務審）

**需董事會簽核**：
1. 召喚法務角色出 ToS / 隱私政策草案 — **批准 → 召喚法務**
2. 前端 onboarding 加同意 checkbox（不算大工程，1 day）— **批准 → CTO 排入下 sprint**

---

## 議題 E：Retention 觸發 — Sprint 7 鋪好基礎，誰啟動？

### 現狀（CTO 線交付物）

- ✅ `/today/reviews` SM-2 due 鷹架列表（T53）
- ✅ 信心度校準趨勢視覺（T63）
- ✅ Daily quest（已存在）
- ✅ Streak counter（已存在）
- ❌ **Email / Push 觸發**：沒有任何「主動拉用戶回來」機制

### 風險

- 用戶當日忘記登入 → SM-2 due 累積 → 之後感受到「補不完」直接放棄
- streak 段位掉了沒有挽回流程

### 選項

- **E1**：Email 觸發（最便宜 — SendGrid free tier 100 mail/day 對 MAU < 1000 夠）
  - 每日 morning 8am：「今日有 X 個重點要複習」
  - 每週日：weekly_reports 寄送（已有 ORM table 但無寄送）
  - streak 斷掉前 2h 提醒
- **E2**：Push notification（Firebase FCM 免費，但 PWA 設定工作量大）
- **E3**：LINE / Telegram bot 整合（台灣用戶 LINE 命中率 90%+，但需另寫 bot）

### 推薦

**E1 先做，2 週內**。已有 Email 寄送基礎（SendGrid 已接 password reset email），只需加 cron + template。

**需董事會簽核**：
1. 召喚客戶成功角色設計 4 個 email template（daily / weekly / streak / due） + 寄送頻率 — **批准 → 召喚客戶成功 + 內容**
2. CTO 線寫 cron job 寄送（FastAPI 排程任務 + SendGrid SDK）— 1 sprint

---

## 董事會（Simon）決策清單彙整

請就以下 5 議題簽核（每項標 ✅ 批准 / ⏸️ 暫緩 / ❌ 拒絕）：

| # | 議題 | 推薦 | 召喚角色 | 預估工作量 | $ 成本 | 風險 |
|---|------|------|----------|-----------:|-------:|------|
| A | 訂閱配額調整 | ⏸️ 暫不動，等 C 數據 | - | - | - | 低 |
| B1 | LLM 毛利儀表板 | ✅ 本 sprint | 財務 + 後端 | 1 sprint | $0 | 低 |
| B2 | ULTRA fair-use cap | ✅ 本 sprint | 法務 + 產品 | 0.5 sprint | $0 | 中（有用戶溝通） |
| C | PostHog onboarding 埋點 | ✅ 本 sprint | 產品 + 前端 | 1 週 | $0 | 低 |
| D | 法務最小最緊清單 | ✅ 1 週內 | 法務 + 前端 | 1 sprint | $0 | 高（不做有罰款風險） |
| E | Email retention 觸發 | ✅ 2 週內 | 客戶成功 + 內容 + 後端 | 2 sprint | $0 | 中 |

**建議啟動順序**：D（法務最緊）→ B1+C（數據基礎）→ B2（防爆）→ E（成長飛輪）

---

**下一步**：等 Simon 對上表逐項簽核，按啟動順序召喚對應 L2 角色展開。
