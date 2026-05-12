# encoding: utf-8
# orphan_coach.feature — #9 AI 蘇格拉底教練對話
# BDD Tags: @backend（所有 Scenario 為後端 API 測試）
# Scenarios 需要真實 LLM 的標記 @ignore（mock/stub 版本通過）

Feature: AI 蘇格拉底教練對話（Orphan 節點）
  As a 學習者
  I want to 與 AI 蘇格拉底教練對話來探索 orphan 節點
  So that 在缺乏學習鷹架時仍能獲得引導式學習體驗

  Background:
    Given 系統中有以下使用者帳號：
      | Email                  | 訂閱方案 | 角色 |
      | pro_user@example.com   | PRO      | user |
      | free_user@example.com  | FREE     | user |
      | pro_plus@example.com   | PRO_PLUS | user |
    And 科目「資訊安全概論」存在
    And 知識節點「零信任架構」屬於科目「資訊安全概論」

  # ── C.1 啟動對話 ──────────────────────────────────────────────────

  @backend
  Scenario: 啟動對話成功（PRO 使用者、有效節點）
    Given 使用者 pro_user@example.com 已認證
    When 我啟動節點「零信任架構」的蘇格拉底對話
    Then HTTP 狀態碼應為 201
    And 回應應包含 conversation_id
    And 回應應包含 opening_message
    And 對話應在 DB 中存在並為 socratic_orphan 模式

  @backend
  Scenario: 啟動對話失敗 — 節點不存在（404）
    Given 使用者 pro_user@example.com 已認證
    When 我啟動一個不存在節點（UUID 隨機）的蘇格拉底對話
    Then 操作失敗，狀態碼為 404

  @backend
  Scenario: 啟動對話失敗 — 未認證（401）
    When 我向 /api/v1/orphan-coach/conversations 發送未認證 POST 請求，body 為 {"node_id": "00000000-0000-0000-0000-000000000000"}
    Then 操作失敗，狀態碼為 401

  # ── C.4.4 暫停接續 ────────────────────────────────────────────────

  @backend
  Scenario: 查詢進行中對話（C.4.4 暫停接續）
    Given 使用者 pro_user@example.com 已認證
    And 使用者已有一個進行中的蘇格拉底對話（節點為 node_id，輪數 2 輪）
    When 我查詢節點的進行中對話
    Then HTTP 狀態碼應為 200
    And 回應應包含 existing_conversation_id
    And existing_conversation_id 不為 null

  @backend
  Scenario: 查詢進行中對話 — 無對話時回傳 null
    Given 使用者 pro_user@example.com 已認證
    When 我查詢節點的進行中對話
    Then HTTP 狀態碼應為 200
    And 回應應包含 existing_conversation_id
    And existing_conversation_id 為 null

  # ── 訊息發送 ──────────────────────────────────────────────────────

  @backend
  Scenario: 發送空訊息應回傳 422
    Given 使用者 pro_user@example.com 已認證
    And 使用者已有一個進行中的蘇格拉底對話（節點為 node_id，輪數 1 輪）
    When 我發送空訊息到蘇格拉底對話
    Then 操作失敗，狀態碼為 422

  @backend
  Scenario: 他人對話不可存取（403）
    Given 使用者 pro_user@example.com 已認證
    And 使用者已有一個進行中的蘇格拉底對話（節點為 node_id，輪數 1 輪）
    When 我以其他使用者身分查詢此蘇格拉底對話
    Then 操作失敗，狀態碼為 403

  # ── 對話詳情 ──────────────────────────────────────────────────────

  @backend
  Scenario: 取得對話詳情
    Given 使用者 pro_user@example.com 已認證
    And 使用者已有一個進行中的蘇格拉底對話（節點為 node_id，輪數 2 輪）
    When 我查詢蘇格拉底對話詳情
    Then HTTP 狀態碼應為 200
    And 回應應包含 messages 清單
    And mastery_committed 應為 false

  # ── 暫停對話 ──────────────────────────────────────────────────────

  @backend
  Scenario: 手動暫停對話
    Given 使用者 pro_user@example.com 已認證
    And 使用者已有一個進行中的蘇格拉底對話（節點為 node_id，輪數 1 輪）
    When 我暫停蘇格拉底對話
    Then HTTP 狀態碼應為 200
    And 回應應包含 paused 欄位

  # ── LLM 分層策略（mock/stub 驗證 model_used 欄位）────────────────

  @backend
  Scenario: PRO 使用者啟動對話應使用 Haiku 模型
    Given 使用者 pro_user@example.com 已認證
    When 我啟動節點「零信任架構」的蘇格拉底對話
    Then HTTP 狀態碼應為 201
    And model_used 應為 claude-haiku-4-5-20251001

  @backend
  Scenario: PRO+ 使用者啟動對話應使用 Sonnet 模型
    Given 使用者 pro_plus@example.com 已認證
    When 我啟動節點「零信任架構」的蘇格拉底對話
    Then HTTP 狀態碼應為 201
    And model_used 應為 claude-sonnet-4-6

  # ── 需要真實 LLM 的 Scenario（@ignore，CI 跳過）─────────────────

  # ── pgvector 失敗防禦（Issue: 蘇格拉底 500 hot-fix）────────────────

  @backend
  Scenario: pgvector 查詢失敗時 start_conversation 仍應成功（issue 蘇格拉底 500）
    Given 使用者 pro_user@example.com 已認證
    And mock pgvector cosine 查詢拋出 InternalError
    When 我啟動節點「零信任架構」的蘇格拉底對話（含 pgvector mock）
    Then HTTP 狀態碼應為 201
    And 回應應包含 conversation_id
    And 回應應包含 opening_message

  @backend @ignore
  Scenario: 多輪正向收尾 — 3 輪且兩輪 ≥ 1.5/2.5 → mastery 降權更新
    # 需要真實 Anthropic API key
    Given 使用者 pro_user@example.com 已認證
    When 我啟動節點「零信任架構」的蘇格拉底對話
    And 我向蘇格拉底對話發送訊息「零信任架構是一種不預設任何使用者或設備可信的安全模型，需要持續驗證每一次存取請求，是現代雲端安全的重要概念」
    And 我向蘇格拉底對話發送訊息「這個概念和傳統的內網信任不同，核心在於『永遠不信任、永遠驗證』，通過身份認證和最小權限原則實施」
    And 我向蘇格拉底對話發送訊息「它也和微分段技術結合，限制橫向移動，確保即使攻擊者進入內網也無法輕易擴散」
    Then 對話應在 DB 中存在並為 socratic_orphan 模式
    And 我查詢蘇格拉底對話詳情
    And mastery_committed 應為 true

  @backend @ignore
  Scenario: 5 輪零接觸度 → 轉介書籍
    # 需要真實 Anthropic API key
    Given 使用者 pro_user@example.com 已認證
    When 我啟動節點「零信任架構」的蘇格拉底對話
    And 我向蘇格拉底對話發送訊息「我不知道」
    And 我向蘇格拉底對話發送訊息「不清楚」
    And 我向蘇格拉底對話發送訊息「沒概念」
    And 我向蘇格拉底對話發送訊息「?」
    And 我向蘇格拉底對話發送訊息「不懂」
    Then 回應應包含 assistant_reply
    And 回應的 status 應為「transfer_book」

  @backend @ignore
  Scenario: 8 輪強制結束
    # 需要真實 Anthropic API key
    Given 使用者 pro_user@example.com 已認證
    And 使用者已有一個進行中的蘇格拉底對話（節點為 node_id，輪數 7 輪）
    When 我向蘇格拉底對話發送訊息「這是第八輪的回覆，我對零信任架構的理解有所加深了」
    Then 回應應包含 assistant_reply
    And 回應的 status 應為「force_end_8_rounds」
