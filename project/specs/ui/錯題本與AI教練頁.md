# 錯題本與 AI 教練頁

## 描述
CertiMate 核心護城河，透過 AI 蘇格拉底教練進行錯題觀念重塑，同時為免費用戶最強升級入口。

## 行為
### 科目切換器（頂部）
- SubjectSwitcher 下拉選單，切換後錯題列表僅顯示該科目

### 錯題導覽清單（左側 Sidebar）
- 條列本次測驗（透過 examId query param）或歷史累積的答錯題目
- 顯示錯誤選項標籤（如「錯選 C」）

### Free 用戶視角（Upsell Funnel）
- 上半可見：題目原文 + 正確答案 vs 使用者選項 + 一句極簡提示
- 下半遮擋：毛玻璃 Glassmorphism 覆蓋，中央解鎖卡片：
  - 「解鎖 AI 智能教練深度解析，每月僅需 199 TWD」+ 升級按鈕

### Pro/Ultra 用戶視角（Deep Dive）
- **靜態詳解**：Markdown + KaTeX 公式排版、原文溯源（一鍵彈出來源片段或 YouTube 時間軸）、盲點痛擊（指出誘答陷阱）
- **AI 教練對話窗**：
  - 具專屬角色視覺與人格設定
  - 情感支持語氣（依答對率動態調整）
  - 記憶歷程：記住使用者過去卡關點並主動關懷
  - 追問無次數上限（但 10 分鐘內超綱提問達 5 次觸發 30 分鐘冷卻）
  - 防護機制：超出題庫範圍時提示「此問題超出目前題庫範圍」
  - 輸入框下方灰色免責小字

## 參考
- `project/03_Research_and_Development/02_Page_Specifications/錯題本與 AI 教練頁 (Review Book & AI Tutor).md`
