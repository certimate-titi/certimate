@feature_38 @scaffold_pitfall @prompt_routing @sprint_2_p1
Feature: 學習鷹架迷思警示與檔案類型分流（端對端 UX）
  作為學習者，我想要在閱讀教材時被警示常見迷思，
  以避免錯誤心智模型固化（Misconception Correction）。

  作為平台，我想要根據檔案類型自動選對的 prompt，
  例如考古題不寫 takeaway（避免洩答）、影片帶時間戳。

  # 對應：
  #   docs/scaffold-redesign-plan.md P1
  #   docs/sprint-2-cto-plan.md T11-T18
  # 學習科學原理：
  #   - Misconception Correction（pitfall）
  #   - Testing Effect 維持（quiz 不洩答）

  Background:
    Given 已存在 PRO 用戶 "alice@example.com" / "alice123"
    And 用戶 "alice@example.com" 已上傳資源 "教材.pdf"
    And 該資源解析狀態為 "success"
    And 該資源含章節 "3.1 No-code 概念" 並含一筆 pitfall 鷹架

  @fullstack
  Rule: PitfallAlert 端對端互動
    Scenario: 章節有 pitfall → 警示卡優先顯示在最上面
      Given 用戶 "alice@example.com" 開啟章節閱讀頁
      Then 章節重點區塊最上方應為「常見迷思」紅色警示卡（aria-label 含「迷思警示卡」）
      And 卡片預設展開（不像 RetrievalCard 摺疊）
      And 卡片含「⚠️」icon + 章節標題 + 對比型內容

    Scenario: 用戶 dismiss 後該卡不再顯示
      Given 用戶 "alice@example.com" 看到 pitfall 警示卡
      When 用戶點擊「關閉警示」X 按鈕
      Then 該章節 pitfall 卡片消失
      And localStorage `certimate_pitfall_dismissed_{scaffold_id}` = "1"
      When 用戶重整頁面
      Then 該卡片仍不顯示（dismiss 持久化）

    Scenario: 資源含影片副檔名 → UI 章節含時間戳格式
      Given 用戶 "alice@example.com" 已上傳 "lecture.mp4"
      And 該資源解析狀態為 "success"
      Then 鷹架 chapter_heading 應符合 "MM:SS-MM:SS …" 格式
      And 鷹架不含 strategy 類型
