@backend
Feature: 完成度框架 — 科目進度計算與徽章里程碑
  依 orphan-mitigation-design.md B.2/B.3/B.4 規格
  以加權 mastery 算出 sweet_spot / full_coverage / sprint_mode 三種進度，
  並判定已解鎖徽章及邊際效益遞減 nudge 觸發條件。

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                | 訂閱方案 | 角色 | 狀態   |
      | u01       | student@test.com     | FREE     | USER | 已啟用 |

  # ─── Scenario 1：全新用戶 — 無 mastery ───────────────────────────────────
  Scenario: 全新用戶科目無 mastery 時三種進度皆為 0 且無徽章
    Given 完成度測試科目 "CompletionSubjectA" 屬於用戶 "student@test.com" 有 3 個頻率為 "5,2,0" 的節點
    And 用戶 "student@test.com" 在科目 "CompletionSubjectA" 無任何 mastery 紀錄
    When 使用者 "student@test.com" 查詢科目 "CompletionSubjectA" 完成度
    Then 回應狀態碼應為 200
    And 完成度回應 sweet_spot_progress 應為 0
    And 完成度回應 full_coverage_progress 應為 0
    And 完成度回應 badges_unlocked 應為空陣列
    And 完成度回應 should_show_marginal_utility_nudge 應為 false

  # ─── Scenario 2：高頻節點 mastery=1.0 — 加權進度提升 ─────────────────────
  Scenario: 高頻節點 mastery 1.0 提升 sweet_spot 進度
    Given 完成度測試科目 "CompletionSubjectA" 屬於用戶 "student@test.com" 有 2 個頻率為 "5,5" 的節點
    And 完成度用戶 "student@test.com" 第 1 個節點 mastery "1.0" SM2間隔 "5" 天
    When 使用者 "student@test.com" 查詢科目 "CompletionSubjectA" 完成度
    Then 回應狀態碼應為 200
    And 完成度回應 sweet_spot_progress 應大於 0
    And 完成度回應 badges_unlocked 包含 "starter"

  # ─── Scenario 3：AI_INFERRED 鷹架 mastery 降權 0.6 ───────────────────────
  Scenario: AI_INFERRED 鷹架 mastery 1.0 計入時降權 0.6 影響 sweet_spot
    Given 完成度測試科目 "CompletionSubjectA" 屬於用戶 "student@test.com" 有 1 個頻率為 "5" 的節點
    And 完成度用戶 "student@test.com" 節點 mastery "1.0" 來源 "AI_INFERRED"
    When 使用者 "student@test.com" 查詢科目 "CompletionSubjectA" 完成度
    Then 回應狀態碼應為 200
    And 完成度回應 sweet_spot_progress 應小於 100
    And 完成度回應 sweet_spot_progress 應大於 0

  # ─── Scenario 4：達 25% 解鎖 explorer 徽章 ───────────────────────────────
  Scenario: sweet_spot 達 25% 解鎖 explorer 徽章
    Given 完成度測試科目 "CompletionSubjectA" 屬於用戶 "student@test.com" 有 4 個頻率為 "2,2,2,2" 的節點
    And 完成度用戶 "student@test.com" 前 1 個節點 mastery "1.5" SM2間隔 "15" 天
    When 使用者 "student@test.com" 查詢科目 "CompletionSubjectA" 完成度
    Then 回應狀態碼應為 200
    And 完成度回應 badges_unlocked 包含 "starter"
    And 完成度回應 badges_unlocked 包含 "explorer"

  # ─── Scenario 5：達 50% 解鎖 builder 徽章 ────────────────────────────────
  Scenario: sweet_spot 達 50% 解鎖 builder 徽章
    Given 完成度測試科目 "CompletionSubjectA" 屬於用戶 "student@test.com" 有 4 個頻率為 "2,2,2,2" 的節點
    And 完成度用戶 "student@test.com" 前 2 個節點 mastery "1.5" SM2間隔 "15" 天
    When 使用者 "student@test.com" 查詢科目 "CompletionSubjectA" 完成度
    Then 回應狀態碼應為 200
    And 完成度回應 badges_unlocked 包含 "builder"

  # ─── Scenario 6：達 85% 解鎖 sweet_spot_achiever 及 nudge 觸發 ─────────────
  Scenario: sweet_spot 達 85% 且距考試 14 天 full_coverage < 100% 觸發 nudge
    Given 完成度測試科目 "CompletionSubjectA" 屬於用戶 "student@test.com" 有 4 個頻率為 "2,2,2,2" 的節點
    And 完成度用戶 "student@test.com" 前 4 個節點 mastery "1.5" SM2間隔 "15" 天
    And 完成度測試科目 "CompletionSubjectA" 額外新增 1 個頻率 "0" 的未覆蓋節點
    And 完成度用戶 "student@test.com" 設定科目 "CompletionSubjectA" 考試日距今 "14" 天
    When 使用者 "student@test.com" 查詢科目 "CompletionSubjectA" 完成度
    Then 回應狀態碼應為 200
    And 完成度回應 badges_unlocked 包含 "sweet_spot_achiever"
    And 完成度回應 should_show_marginal_utility_nudge 應為 true

  # ─── Scenario 7：空科目（無節點）— 不報錯回 0 ───────────────────────────
  Scenario: 空科目無節點時完成度回 0 且不報錯
    Given 完成度測試科目 "EmptySubject" 屬於用戶 "student@test.com" 無節點
    When 使用者 "student@test.com" 查詢科目 "EmptySubject" 完成度
    Then 回應狀態碼應為 200
    And 完成度回應 sweet_spot_progress 應為 0
    And 完成度回應 full_coverage_progress 應為 0
    And 完成度回應 badges_unlocked 應為空陣列

  # ─── Scenario 8：跨科目隔離 — A 科目 mastery 不影響 B ────────────────────
  Scenario: 跨科目隔離 A 科目 mastery 不影響 B 科目進度
    Given 完成度測試科目 "CompletionSubjectA" 屬於用戶 "student@test.com" 有 2 個頻率為 "5,5" 的節點
    And 完成度測試科目 "SubjectB" 屬於用戶 "student@test.com" 有 2 個頻率為 "5,5" 的節點
    And 完成度用戶 "student@test.com" 科目 "CompletionSubjectA" 所有節點 mastery "1.0" SM2間隔 "5" 天
    When 使用者 "student@test.com" 查詢科目 "SubjectB" 完成度
    Then 回應狀態碼應為 200
    And 完成度回應 sweet_spot_progress 應為 0

  # ─── Scenario 9：無 JWT — 401 ────────────────────────────────────────────
  Scenario: 未帶 JWT 查詢完成度回 401
    Given 完成度測試科目 "CompletionSubjectA" 屬於用戶 "student@test.com" 無節點
    When 未認證使用者查詢科目 "CompletionSubjectA" 完成度
    Then 回應狀態碼應為 401

  # ─── Scenario 10：科目不存在 — 404 ──────────────────────────────────────
  Scenario: 查詢不存在科目完成度回 404
    When 使用者 "student@test.com" 查詢科目 "00000000-0000-0000-0000-000000000000" 完成度
    Then 回應狀態碼應為 404
