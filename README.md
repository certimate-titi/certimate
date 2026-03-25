# CertiMate 證照考試學習平台

![CertiMate Banner](project/CertiMate_Logo.png) <!-- 建議上傳 Logo 後替換此連結 -->

CertiMate 是一個整合 AI 技術的證照學習與考試資源平台。旨在透過人工智慧自動化解析龐雜的學習資料，生成心智圖、模擬考題與個人化複習計畫，成為使用者備考路上的最佳陪伴者。

---

## 核心功能 (Core Features)

- **AI 資源解析**：上傳 PDF、圖片或連結，由 AI 自動萃取重點並轉換為可讀性高的 Markdown 格式。
- **知識心智圖**：視覺化學習地圖，自動生成知識節點並提供導覽功能。
- **模擬機考系統**：根據學習內容自動生成符合考綱的模擬試題，提供即時回饋。
- **錯題複習與 AI 教練**：針對弱點進行 AI 引導式教學，結合艾賓浩斯遺忘曲線安排複習排程。
- **B2B 機構管理**：提供機構管理員批量管理學員、派發測驗與查看班級分析熱點圖。
- **異常維修管理**：系統自動追蹤錯誤，並提供透明的維修排程與通告機制。

---

## 技術架構 (Technology Stack)

- **前端 (Frontend)**: Next.js 15 (App Router), TypeScript, Tailwind CSS, ShadcnUI
- **後端 (Backend)**: Node.js, Firebase (Firestore, Auth, Storage, Functions)
- **AI 整合**: Gemini 1.5 Pro/Flash, Claude 3.5 Sonnet (透過 Vertex AI / API)
- **基礎設施**: Google Cloud Platform (GCP), Firebase Hosting
- **開發流程**: TDD (Test Driven Development), Gherkin Feature Specs

---

## 目錄結構 (Folder Structure)

```text
certimate/
├── frontend/           # Next.js 前端應用程式
├── project/            # 專案規劃、市場分析與規格文件
│   ├── features/       # Gherkin 功能規格 (.feature)
│   ├── specs/          # 系統架構、資料庫綱要與流程設計
│   └── 01_Management/  # 專案管理、報價與 Roadmap
├── CLAUDE.md           # AI 輔助開發指令與規範
└── README.md           # 本文件
```

---

## 如何開始 (Getting Started)

### 前端開發
1. 進入 `frontend` 目錄:
   ```bash
   cd frontend
   ```
2. 安裝依賴:
   ```bash
   npm install
   ```
3. 啟動開發伺服器:
   ```bash
   npm run dev
   ```

---

## 聯絡與授權

© 2026 CertiMate Team. All Rights Reserved.
