@backend
Feature: F47 — YouTube 雙路徑分流 Pipeline
  YouTube 上傳依 CC 字幕可用性分流：
  - 有 CC（subtitles / automatic_captions）→ VTT 下載 + Gemini 2.5 Flash 結構化（消耗 1 份配額）
  - 無 CC → Gemini 2.5 Pro 直餵 YouTube URL（消耗 5 份配額）
  長度上限：有 CC 60 分鐘 / 無 CC 20 分鐘。
  無 CC 路徑有月度成本封頂（PRO USD 3 / PRO_PLUS USD 12）。

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                      | 訂閱方案 |
      | 1        | pro_user@example.com       | PRO      |
      | 2        | pro_plus_user@example.com  | PRO_PLUS |
    And 使用者 "pro_user@example.com" 備考科目為 "計算機概論"（科目 ID: 1）
    And 使用者 "pro_plus_user@example.com" 備考科目為 "計算機概論"（科目 ID: 1）

  # Rule 1: 有 CC → Flash text path
  Rule: 有 CC 路徑走 Flash 文字結構化

  @backend
  Scenario: subtitles 非空時不送 Gemini video API
    When 使用者 "pro_user@example.com" 提交有 CC 字幕的 YouTube URL，科目為 1
    Then 操作成功
    And YouTube 擷取器使用 Flash 文字路徑，不呼叫 Gemini File API

  @backend
  Scenario: 有 CC 路徑配額消耗 1 份
    Given 使用者 "pro_user@example.com" 本月已完成 0 次 LLM 資源解析
    When 使用者 "pro_user@example.com" 提交有 CC 字幕的 YouTube URL，科目為 1
    Then 操作成功
    And 使用者 "pro_user@example.com" 本月 YouTube 配額已消耗 1 份

  # Rule 2: 無 CC → Pro video path
  Rule: 無 CC 路徑走 Gemini Pro 直餵

  @backend
  Scenario: subtitles 與 auto_captions 皆空時送 Gemini File API
    When 使用者 "pro_user@example.com" 提交無 CC 字幕的 YouTube URL，科目為 1
    Then 操作成功
    And YouTube 擷取器使用 Pro 直餵路徑

  @backend
  Scenario: 無 CC 路徑配額消耗 5 份
    Given 使用者 "pro_user@example.com" 本月已完成 0 次 LLM 資源解析
    When 使用者 "pro_user@example.com" 提交無 CC 字幕的 YouTube URL，科目為 1
    Then 操作成功
    And 使用者 "pro_user@example.com" 本月 YouTube 配額已消耗 5 份

  # Rule 3: 長度上限分流
  Rule: 長度上限依路徑分流（有 CC 60 分 / 無 CC 20 分）

  @backend
  Scenario: 有 CC + 50 分鐘通過
    When 使用者 "pro_user@example.com" 提交有 CC 且 50 分鐘的 YouTube URL，科目為 1
    Then 操作成功

  @backend
  Scenario: 有 CC + 65 分鐘超過上限
    When 使用者 "pro_user@example.com" 提交有 CC 且 65 分鐘的 YouTube URL，科目為 1
    Then 操作失敗，狀態碼為 422
    And 錯誤訊息應包含 "不可超過 60 分鐘"

  @backend
  Scenario: 無 CC + 18 分鐘通過
    When 使用者 "pro_user@example.com" 提交無 CC 且 18 分鐘的 YouTube URL，科目為 1
    Then 操作成功

  @backend
  Scenario: 無 CC + 22 分鐘超過上限
    When 使用者 "pro_user@example.com" 提交無 CC 且 22 分鐘的 YouTube URL，科目為 1
    Then 操作失敗，狀態碼為 422
    And 錯誤訊息應包含 "不可超過 20 分鐘"

  # Rule 4: 月度成本封頂
  Rule: 無 CC 路徑月度成本封頂

  @backend
  Scenario: PRO 用戶月成本超過 USD 3 上限，無 CC 新影片被拒絕
    Given 使用者 "pro_user@example.com" 本月 AI 成本已累積 USD 2.80
    When 使用者 "pro_user@example.com" 提交無 CC 字幕的 YouTube URL，科目為 1
    Then 操作失敗，狀態碼為 422
    And 錯誤訊息應包含 "成本已接近方案上限"

  # Rule 5: 不依賴 Whisper
  Rule: YouTube 擷取不依賴 openai whisper

  @backend
  Scenario: YouTube 提交走 Gemini path，不依賴 openai whisper 模組
    When 使用者 "pro_user@example.com" 提交無 CC 字幕的 YouTube URL，科目為 1
    Then 操作成功
    And YouTube 擷取器不匯入 openai whisper 模組

  # Rule 6: 配額退回
  Rule: EnqueueFailedError 退回配額

  @backend
  Scenario: PRO 用戶剩餘 4 份配額，無 CC 上傳失敗（需 5 份）
    Given 使用者 "pro_user@example.com" 本月已完成 46 次 LLM 資源解析
    When 使用者 "pro_user@example.com" 提交無 CC 字幕的 YouTube URL，科目為 1
    Then 操作失敗，狀態碼為 402
    And 錯誤訊息應包含 "配額"

  @backend
  Scenario: 有 CC 上傳失敗時配額退回（用量歸零）
    Given 使用者 "pro_user@example.com" 本月已完成 0 次 LLM 資源解析
    When 使用者 "pro_user@example.com" 提交有 CC 且排程失敗的 YouTube URL，科目為 1
    Then 操作失敗，狀態碼為 503
    And 使用者 "pro_user@example.com" 本月 YouTube 配額已退回（用量為 0）

  @backend
  Scenario: 無 CC 上傳失敗時配額退回（用量歸零）
    Given 使用者 "pro_user@example.com" 本月已完成 0 次 LLM 資源解析
    When 使用者 "pro_user@example.com" 提交無 CC 且排程失敗的 YouTube URL，科目為 1
    Then 操作失敗，狀態碼為 503
    And 使用者 "pro_user@example.com" 本月 YouTube 配額已退回（用量為 0）
