# Phase 3: 正式上線與商業擴張詳解

## M7 (10月)：v1.0 正式上線

### 資安防護與架構鞏固 (Security & Hardening)
- **Anti-DDoS 防護網**：在 Cloud Run 加上 Google Cloud API Gateway 或 Firebase App Check，嚴格限制未經驗證的惡意流量。
- **API 速率限制 (Rate Limiting)**：以 Redis 實作進階 Rate Limit。10 分鐘內觸發 5 次惡意問答的使用者，強制冷卻 30 分鐘；超額使用 Claude 教練的行為則由配額守門員阻斷，不追加計費。
- **正式環境切換**：清除所有 Beta 假帳號與沙盒金流資料，API 端點正式指向 Production 環境。

### 行銷與 SEO (Marketing & SEO)
- **SEO 結構化佈署**：對 Next.js 所有公開頁面（Landing Page、Pricing、Features）補齊 `<meta>` tags、`og:image`，自動生成 `sitemap.xml`。
- **Landing Page 優化**：升級首頁，展示三階層定價（Pro / Pro Plus / Ultra），強調「省時、錯題歸因、AI 教練補破洞」的核心痛點，並放入 Beta 期間優質用戶見證 (Testimonials)。
- **首波宣傳**：透過各大社群與 KOL 進行開台第一波宣發。

## M8 (11月)：商業模式優化與資料智能

### 轉換率與留存率優化 (CRO & Retention)
- **毛玻璃 Paywall 漏斗分析**：追蹤「知識心智圖 AI 教練鎖頭點擊 → 升級 Pro Plus 付款成功」的轉換率，A/B 測試不同升級提示文案與按鈕位置。
- **Sprint / Standard / Mastery 動態排程上線**：正式啟用三模式動態學習演算法，根據距離考試天數自動切換排題策略，並透過 Mixpanel 驗證此功能對留存率 (Retention) 的實際提升效果。
- **艾賓浩斯推播**：利用 Google Cloud Scheduler 每日定時掃描用戶錯題歷史，透過 Email 寄出「這幾題你上週答錯，現在是複習的最佳時機」，提升回訪率。

### 多元變現管道 (Monetization Engine)
- **免費用戶廣告變現**：為 Free 用戶版面植入 Google AdSense 或教育聯播網廣告，以廣告收入打平免費用戶的基礎算力成本。

## M9 (12月)：B2B SaaS 啟航 (Ultra 方案機構後台)

### 機構管理後台（Ultra 方案限定）
- **席位派發 (Seat Management)**：Ultra 方案管理員可將機構授權名額派發給學生子帳號，並透過 CSV 批次匯入學員名單（含個資法合規同意流程）。
- **班級弱點熱力圖 (Class Heatmap)**：機構管理員可查看全班各知識節點的答對率熱力圖，即時掌握哪個章節最弱，輔助備課決策。
- **早期預警系統 (Early Warning)**：自動偵測平均分低於 60 分、連續 3 次成績下滑或 5 天未登入的學員，浮出需關注清單，讓教師主動介入。
- **AI 個人化補強建議**：管理員可為特定學員觸發 Claude 基於弱點節點生成 1-3 條具體補強建議（review / quiz / explore 動作類型）。
- **考卷派發**：機構管理員自製題庫考卷後，可指定群組並設定截止日期強制派卷。

### 多租戶架構 (Multi-Tenancy)
- **資料隔離**：確保補習班 A 的學員資料在 PostgreSQL Schema 或 Row-Level Security 層面完全隔離於補習班 B，防止跨租戶資料洩漏。

### 平台超級管理後台 (Super Admin Dashboard)
- **AI 成本燃燒圖**：即時追蹤各 LLM 模型（Gemini Flash / Claude / GPT-4o）的 Token 消耗與費用趨勢，作為模型路由決策依據。
- **異常用戶偵測**：自動標記短時間內大量上傳或共用帳號行為的可疑使用者，提供一鍵封鎖功能。
- **Feature Flag 管控**：Super Admin 可透過後台對特定功能設定灰度上線比例（如新版 AI 教練 v2 僅對 20% 用戶開放），降低大版本上線風險。
