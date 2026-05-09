@backend
Feature: AI 補洞鷹架（Orphan Auto-Fill Scaffold）
  作為學生，當我在知識心智圖中看到 orphan 節點（無學習鷹架），
  系統可以從考古題反推並自動生成 AI 補洞鷹架（K-ORPHAN-01 模板）。
  AI 生成的內容必須有足夠佐證題支撐，並且信心低時顯示警告。
  學生可標記不準確；累積 ≥3 份回報則自動觸發人工審核。

  Background:
    Given 一位已驗證的學生帳號 "orphan_student@test.com"
    And 一個科目有 50 題考古題 "信義原則應用"
    And 科目下有一個 depth=2 的 orphan 節點 "信義原則" 無任何 scaffold_node_link

  @backend @ignore
  Scenario: 成功生成 AI 補洞鷹架（佐證 ≥3、信心分數通過）
    # 需要有效的 ANTHROPIC_API_KEY；CI 環境加 @ignore 跳過真實 LLM 呼叫
    Given 節點 "信義原則" 有 5 題對應考古題（精確命中）
    When 學生 "orphan_student@test.com" 請求節點 "信義原則" 的 orphan scaffold
    Then 系統以 AI_INFERRED trust_level 回傳鷹架
    And 鷹架包含 definition、illustration、practice_question 三段
    And confidence_score 在 31 到 100 之間
    And 鷹架的 template_code 為 "K-ORPHAN-01"

  @backend
  Scenario: 佐證題不足（<3 題）時拒絕生成
    Given 節點 "信義原則" 只有 2 題對應考古題
    When 學生 "orphan_student@test.com" 請求節點 "信義原則" 的 orphan scaffold
    Then 系統回應 422
    And 回應包含 fail_safe 欄位為 true
    And 回應訊息包含 "佐證題不足"

  @backend
  Scenario: 信心分數計算 — 5 題精確命中
    When 計算信心分數：evidence_count=5，exact_hit_ratio=0.8，distance_decay=0.0
    Then 信心分數為 40

  @backend
  Scenario: 信心分數計算 — 8 題（上限）精確命中
    When 計算信心分數：evidence_count=8，exact_hit_ratio=1.0，distance_decay=0.0
    Then 信心分數為 80

  @backend
  Scenario: 信心分數計算 — 10 題（超過上限計 8）
    When 計算信心分數：evidence_count=10，exact_hit_ratio=1.0，distance_decay=0.0
    Then 信心分數為 80

  @backend
  Scenario: 學生標記 AI 鷹架不準確（單次回報 → 個人記錄）
    Given 節點 "信義原則" 已有 AI_INFERRED 鷹架
    When 學生 "orphan_student@test.com" 回報鷹架 "definition_wrong" 原因不準確
    Then 系統回應 200
    And scaffold_review_queue 有 1 筆回報
    And 鷹架的 trust_level 仍為 "AI_INFERRED"（尚未達門檻）

  @backend
  Scenario: 同一鷹架收到 ≥3 份不同用戶回報後自動進入審核
    Given 節點 "信義原則" 已有 AI_INFERRED 鷹架
    And 另外 2 個學生帳號 "reporter2@test.com" 和 "reporter3@test.com"
    And "reporter2@test.com" 已回報鷹架 "example_wrong"
    And "reporter3@test.com" 已回報鷹架 "unrelated"
    When 學生 "orphan_student@test.com" 回報鷹架 "answer_wrong" 原因不準確
    Then 系統回應 200
    And 回應中 already_pending 為 true
    And 鷹架的 trust_level 變更為 "PENDING_REVIEW"

  @backend
  Scenario: 重複回報同一鷹架應被拒絕
    Given 節點 "信義原則" 已有 AI_INFERRED 鷹架
    And 學生 "orphan_student@test.com" 已回報過此鷹架
    When 學生 "orphan_student@test.com" 再次回報同一鷹架
    Then 系統回應 409
    And 回應訊息包含 "已回報過"

  @backend
  Scenario: 已有 cache 的節點直接回傳不重複生成
    Given 節點 "信義原則" 已有 AI_INFERRED 鷹架
    When 學生 "orphan_student@test.com" 請求節點 "信義原則" 的 orphan scaffold
    Then 系統回應 200
    And 回應中 is_cached 為 true

  @backend
  Scenario: admin 可查看審核佇列
    Given 一位管理員帳號 "admin@test.com"
    And 節點 "信義原則" 已有 AI_INFERRED 鷹架被 3 位不同用戶回報
    When 管理員查詢 orphan scaffold 審核佇列
    Then 系統回應 200
    And 回應中 items 列表非空
    And 每筆 item 包含 scaffold_id、report_count、reason_codes

  @backend
  Scenario: 非 admin 用戶無法查看審核佇列
    When 學生 "orphan_student@test.com" 查詢 orphan scaffold 審核佇列
    Then 系統回應 403
