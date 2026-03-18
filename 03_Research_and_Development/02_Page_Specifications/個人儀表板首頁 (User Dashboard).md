# 個人儀表板首頁 (User Dashboard)


## 📌 頁面定位與目標

作為使用者登入後的第一個主畫面，這是 CertiMate 系統的指揮中心。目標是讓使用者能 **一眼掌握學習進度 (Progress Tracking)** 並提供 **最直覺的核心操作入口 (Quick Actions)**。

## 🧩 核心區塊設計 (Sections)

### 1. 歡迎與概覽區 (Welcome & Overview)

- **個人化問候**：例如 "Ready to crush your PMP exam, Alex?"
- **核心指標卡片 (Metric Cards)**：
  - 即將到來的考試倒數計時器。
  - 累積完成的模擬題數。
  - 整體系統預測的及格率 / 答對率區間。
- **能力分佈雷達圖 (Skill Radar)**：利用 Chart.js 等圖表套件，展示各大知識領域的強弱項。

### 2. 快速上傳區 (Upload Widget)

這是此頁面最重要的行動呼籲 (Call to Action)，採用大面積的拖曳區塊與分頁設計：

- **Tab A (實體檔案)**：支援拖曳或點選上傳 PDF、Markdown 或螢幕截圖/手寫照片。
- **Tab B (影音連結)**：
  - 一個居中放大的 URL 輸入框。
  - 「一鍵解析與生成心智圖」的超大按鈕。
- **狀態回饋**：當上傳或解析中時，必須提供平滑的進度條或 Skeleton 骨架屏動畫。

### 3. 動態提醒與待辦清單 (Action Items)

依據使用者的學習行為，由系統動態產生的建議清單：

- **近期錯題複習**：例如 3 天前做錯的 15 題，提示「依照遺忘曲線，現在是複習的最佳時機」。
- **未完成的考卷**：顯示上次中斷的模擬測驗進度 (例如 "AWS SAA Mock #3 - 50% Completed")。
- **新解析完成的講義**：提示知識心智圖已生成完畢，點擊查看。

### 4. 側邊導覽列 (Sidebar Navigation)

全站通用的側邊欄，包含：

- 🏠 儀表板 (Dashboard)
- 📚 資源庫與心智圖 (Knowledge Base)
- 📝 模擬測驗 (Mock Exams)
- 📖 錯題本 (Review Book)
- ⚙️ 設定與訂閱 (Settings)

## 💻 技術面/實作建議

- **資料預取 (Data Fetching)**：這頁的圖表與數據較多，建議使用 SWR 或 React Query 進行快取與 Optimistic UI 更新。
- **RWD (響應式設計)**：雷達圖與上傳區塊在手機端需要調整堆疊順序，確保上傳區塊始終在第一屏可見。

