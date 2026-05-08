# language: zh-TW
@feature_43 @semantic_search @ia_migration @sprint_6_p5 @backend
Feature: Voyage 語意搜尋 + /today 整合 + IA 軟性遷移（後端契約）
  覆蓋 Sprint 6 P5 T47-T49 後端：
  - /today 加 scaffold_due_count
  - /concept-center 加 Voyage rerank
  - /dashboard 加 banner（前端，project/ side）

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"

  @backend
  Rule: /today 整合 SM-2 due
    Scenario: 回應含 scaffold_due_count 欄位
      Given 用戶 alice 有 0 個 SM-2 due 鷹架
      When GET /dashboard/today
      Then 回 200，scaffold_due_count = 0
      And TodayResponse schema 含 scaffold_due_count 欄

    Scenario: 鷹架到期 + 答錯題並存 → review 卡片合併標題
      Given 用戶 alice 有 5 個 due 鷹架 + 3 題答錯
      When GET /dashboard/today
      Then items 含 kind=review，title 為「複習 5 個重點 + 3 題錯題」

    Scenario: 只有鷹架到期，無答錯題 → review 卡片獨立顯示
      Given 用戶 alice 有 7 個 due 鷹架，0 題答錯
      Then items review 卡片 title 為「複習 7 個鷹架重點」
      And href = "/today/reviews"

  @backend
  Rule: /concept-center Voyage rerank
    Scenario: semantic=true（default）→ 用 Voyage rerank
      Given 用戶 alice 有 100+ scaffolds 含「機器學習」
      When GET /concept-center?q=機器學習
      Then 回 200，hits 按語意相似度排序
      And X-Tier-Quota-Remaining 響應 header 預期未來會加（Sprint 7）

    Scenario: semantic=false → 純 ILIKE 順序
      When GET /concept-center?q=機器學習&semantic=false
      Then 回 200，hits 按 (pitfall asc, created_at desc) 順序

    Scenario: voyage 失敗自動 fallback ILIKE
      Given Voyage API key 無效或 quota 用盡
      When GET /concept-center?q=機器學習
      Then 回 200（不阻斷），fallback ILIKE 順序
      And log 含 "voyage rerank failed, fallback ILIKE order"
