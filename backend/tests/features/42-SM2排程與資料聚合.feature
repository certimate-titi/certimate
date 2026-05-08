# language: zh-TW
@feature_42 @sm2 @today_aggregation @concept_center @sprint_5_p4 @backend
Feature: SM-2 排程 + /today 聚合 + 概念中心（後端契約）
  覆蓋 Sprint 5 P4 T41-T45 後端：
  - SM-2 spaced repetition 演算法
  - GET /dashboard/today 學習首頁聚合
  - GET /concept-center 跨資源搜尋
  - K-06 v7 interleaving prompt

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"

  @backend
  Rule: SM-2 演算法
    Scenario: 連 3 次 full → interval 1d → 6d → 17d
      Given 用戶對 scaffold "sf-1" 第 1 次 quality=full
      Then SM-2 排程 next_review_at = today + 1d, repetitions = 1, ease_factor ≈ 2.6
      When 用戶第 2 次 quality=full
      Then next_review_at = today + 6d, repetitions = 2, ease_factor ≈ 2.7
      When 用戶第 3 次 quality=full
      Then next_review_at = today + 17d (round(6 * 2.7)), repetitions = 3

    Scenario: 答錯重置 (none, grade=1) → interval=1d, repetitions=0
      Given 用戶 scaffold sf-1 已 repetitions=2 (full×2)
      When 用戶第 3 次 quality=none
      Then next_review_at = today + 1d, repetitions = 0, ease_factor 下降至 ~2.26

    Scenario: ease_factor 最低 1.3
      Given 用戶連續多次 quality=none
      Then ease_factor 不會降到 1.3 以下

  @backend
  Rule: /scaffold-reviews/due endpoint
    Scenario: 取今日該複習清單
      Given 用戶 alice 有 3 個 scaffold next_review_at <= now
      And 另有 2 個 scaffold next_review_at = 5 天後
      When 用戶 GET /scaffold-reviews/due
      Then 回 200，total=3，items 按 next_review_at 升序

    Scenario: limit 控制
      When 用戶 GET /scaffold-reviews/due?limit=2
      Then items.length ≤ 2

  @backend
  Rule: /dashboard/today 聚合
    Scenario: 用戶有 resource → resume 卡帶最新 COMPLETED 資源
      Given 用戶 alice 有 1 份 COMPLETED resource "res-A"
      When 用戶 GET /dashboard/today
      Then resume.resource_id = res-A
      And items 含 kind="resume" + kind="sprint_exam"
      And 若 review_count > 0 也含 kind="review"

    Scenario: 用戶完全沒資源 → resume 為 null
      Given 用戶 alice 無任何資源
      When 用戶 GET /dashboard/today
      Then resume = null
      And items 不含 kind="resume"
      And items 含 kind="sprint_exam"

  @backend
  Rule: /concept-center 跨資源搜尋
    Scenario: q 至少 2 字 → 200 結果
      Given 用戶 alice 有 scaffolds 含「機器學習」
      When 用戶 GET /concept-center?q=機器學習
      Then 回 200，hits 含對應 scaffold

    Scenario: q 長度 < 2 → 422
      When 用戶 GET /concept-center?q=A
      Then 回 422 含「at least 2 characters」

    Scenario: pitfall 排序最前
      Given 用戶有 takeaway + pitfall 兩種 scaffold 含「No-code」
      When 用戶 GET /concept-center?q=No-code
      Then hits[0].scaffold_type = "pitfall"
