# language: zh-TW
@feature_37 @scaffold_retrieval @sprint_1_p0
Feature: 學習鷹架檢索練習與章節練習（端對端 UX）
  作為學習者，我想要在閱讀學習指引時被引導主動回想，
  以便比直接看答案的記憶保留率更高（Karpicke retrieval practice）。

  # 對應：
  #   docs/scaffold-redesign-plan.md P0
  #   docs/sprint-1-cto-plan.md T08 + T09
  # 學習科學原理：
  #   - Retrieval Practice (Karpicke 1968) — 主動回想保留率比直接讀高 3 倍
  #   - Testing Effect (Roediger & Karpicke 2006) — 章節讀完當下測驗保留率最佳
  # 後端 Rule 細節在 backend/tests/features/37-學習鷹架檢索練習.feature

  Background:
    Given 已存在 PRO 用戶 "alice@example.com" / "alice123"
    And 用戶 "alice@example.com" 已上傳資源 "AI 應用規劃師-科目1.pdf"
    And 該資源解析狀態為 "success" 且 markdown 已存在
    And 該資源含章節 "3.1 人工智慧概念"
    And 章節 "3.1 人工智慧概念" 含 takeaway 鷹架且 retrieval_prompt 非空

  @fullstack
  Rule: 端對端 retrieval-first 互動流程
    Scenario: 用戶讀章節 → 揭曉重點 → 自評回想感
      Given 用戶 "alice@example.com" 開啟 "/library/read/reading?docId={rid}&chapter=ch-2-31-人工智慧概念"
      Then 章節重點區塊預設摺疊狀態
      And 應顯示 "想想看" 文字 + retrieval_prompt 內容
      And 應有「我想完了，看答案」按鈕
      And takeaway 答案內容不應出現在 DOM
      When 用戶點擊「我想完了，看答案」
      Then takeaway content 應顯示
      And 應出現「沒想到 / 想到一半 / 完全想到」三選一
      And scaffold_interaction_log 新增 revealed 事件
      When 用戶點擊「完全想到」
      Then 應顯示「✓ 已紀錄」確認訊息
      And scaffold_interaction_log 新增 recall_self_rated, recall_quality=full

    Scenario: 章節讀完出現 InlinePractice
      Given 章節 "3.1 人工智慧概念" 對應 page_start=15 / page_end=25
      And 該頁碼範圍內有 2 題已核可題目
      When 用戶開啟 "/library/read/reading?docId={rid}&chapter=ch-2-31-人工智慧概念"
      Then 章節 markdown 下方應出現「✅ 章節練習（2 題）」區塊
      And 每題顯示 4 個選項按鈕
      When 用戶點擊正確答案
      Then 應顯示「✓ 答對了！」+ 解析

    Scenario: 解析中態 retrieval-first 不誤導
      Given 用戶 "alice@example.com" 剛上傳新資源 "fresh.pdf" 解析狀態為 "queued"
      When 用戶開啟 "/library/read/reading?docId={fresh_rid}"
      Then 應顯示「⏳ multimodal Pro 解析中」虛線卡片
      And 不應 fallback 渲染舊 chunks 內容
