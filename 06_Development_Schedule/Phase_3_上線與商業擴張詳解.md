# Phase 3: 正式上線與商業擴張詳解

## M7 (10月)：v1.0 正式上線

### 資安防護與架構鞏固 (Security & Hardening)
- **Anti-DDoS 防護網**：在 Cloud Run 前端加上 Google Cloud API Gateway 或 Firebase App Check，嚴格限制未經驗證的流量 (防範惡意腳本與白嫖)。
- **API 速率限制 (Rate Limiting)**：利用 Redis 實作進階的 Rate Limit。例如：「10 分鐘內觸發 5 次不相關惡意問答的使用者，關入小黑屋 30 分鐘不能使用」。
- **正式環境切換**：清空所有 Beta 測試的「假帳號」與「沙盒金流資料」，將所有的 API 端點正式指向 Production 環境。

### 行銷與 SEO (Marketing & SEO)
- **SEO 結構化佈署**：對 Next.js 前端所有的公開頁面 (Landing Page、Pricing、Features) 補齊 `<meta>` tags、`og:image`，並自動生成 `sitemap.xml`。
- **Landing Page 優化**：將原本的 MVP 首頁升級，強調「省錢、省時、高亮錯題」的核心痛點，並放入 Beta 期間的優質用戶見證 (Testimonials)。
- **首波宣傳**：透過各大社群與 KOL 進行開台第一播宣發。

## M8 (11月)：商業模式優化

### 轉換率與留存率優化 (CRO & Retention)
- **漏斗優化 (Funnel Optimization)**：利用 Mixpanel 追蹤「登入 -> 上傳 -> 免費考題生成 -> 遇到進階錯題教練 -> 點擊升級 Pro -> 付款成功」的轉化率，A/B 測試不同的定價引導 UI。
- **艾賓浩斯複習推播**：開發「記憶曲線追蹤」演算法，利用 Google Cloud Scheduler 每日定時掃描用戶錯題歷史，透過 Email 自動寄出「這三題你上週答錯了，花 5 分鐘再複習一下吧！」的信件，提升用戶回訪率 (Retention)。

### 多元變現管道 (Monetization Engine)
- **免費用戶廣告變現**：為 Free 用戶版面植入 Google AdSense 或相關的教育聯播網廣告，達到哪怕不轉 Pro 也能為伺服器打平開銷的最終目的。

## M9 (12月)：B2B SaaS 準備

### 企業端雛型設計 (B2B Prototyping)
- **多租戶架構 (Multi-Tenancy) 評估**：針對補習班、知名企業內訓講師，評估系統架構如何分割資料庫，讓 A 企業的學員資料完全獨立於 B 企業。
- **講師版儀表板 (Instructor Dashboard)**：實作初步的講師端後台，講師可以看見全班學生「哪幾題錯最多」，藉此優化下一次的實體授課品質。
- **B2B 帳號授權系統**：設計「機構大量授權碼 (License Key)」，讓講師能一次購買 50 人份的 Pro 權限批次派發給學員。
