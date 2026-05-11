@feature_41 @advance_organizer @concept_center @sprint_4_p3
Feature: 讀前定錨 + 跨資源概念中心 + 完整 prompt 模板矩陣
  作為學習者，我想要：
  - 在閱讀章節**前**先看到引導問句（建立心智錨點）
  - 跨資源搜尋同一個概念（PDF / 影片 / 考古題的不同呈現）
  - 上傳音訊 / 圖片 / DOCX 都得到對應特化解析

  # 對應：
  #   docs/scaffold-redesign-plan.md P3
  #   docs/sprint-2-cto-plan.md 後續
  # 教學原理：
  #   - Ausubel Subsumption Theory（advance_organizer）
  #   - One Concept, Many Sources（concept-center）
  #   - 多媒材 file-type aware UI

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"

  @fullstack
  Rule: AdvanceOrganizer 讀前定錨 UI
    Scenario: 章節含 advance_organizer 鷹架 → 預設展開顯示在最上方
      Given 用戶 "alice@example.com" 開啟章節閱讀頁
      And 該章節含 type=advance_organizer 鷹架
      Then 章節右側鷹架區**最上方**為紫色「讀前定錨卡」（aria-label="讀前定錨卡"）
      And 卡片預設展開
      And 卡片含「💡 帶著這個問題讀章節」標語

    Scenario: 點「我已思考過，繼續閱讀」→ 摺疊
      Given 用戶看到 advance_organizer 卡片
      When 用戶點擊「我已思考過，繼續閱讀」按鈕
      Then 卡片摺疊為一行小提示（含「點擊重新展開」）
      And localStorage `certimate_organizer_acked_{scaffold_id}` = "1"

  @fullstack
  Rule: 概念中心頁
    Scenario: 搜尋概念 → 跨資源結果分組顯示
      Given 用戶 "alice@example.com" 已上傳多份資源含「No-code」概念
      When 用戶開啟 "/library/concept/concept?subjectId={sid}&q=No-code"
      Then 應顯示搜尋結果分組：
        | 分組 | 內容 |
        | ⚠️ 跨資源迷思彙整 | pitfall scaffolds 含 No-code |
        | 📄 PDF 教材觀點 | takeaway scaffolds 含 No-code |
        | 🎬 影片觀點 | 影片資源 scaffolds 含 No-code |
        | ❓ 考古題 | 考古題資源 scaffolds 含 No-code |

    Scenario: 無結果 → 合理空態
      Given 該科目資源中無「不存在的概念」相關內容
      When 用戶搜尋「不存在的概念」
      Then 顯示「找不到『不存在的概念』的相關鷹架內容」

  # @backend 後端契約見 backend/tests/features/41-讀前定錨與概念中心.feature
  # K-RE-01 逆向工程章節定錨：backend/tests/features/41b-章節級讀前定錨生成.feature
