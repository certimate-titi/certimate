@backend
Feature: F47 — YouTube Gemini Direct Pipeline
  將 yt-dlp / Whisper 依賴完全替換為 Gemini File API 直接處理 YouTube URL。
  YouTube 上傳消耗 2 份解析配額；超過 30 分鐘的影片拒絕。

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                   | 訂閱方案 |
      | 1        | pro_user@example.com    | PRO      |
    And 使用者 "pro_user@example.com" 備考科目為 "計算機概論"（科目 ID: 1）

  # ──────────────────────────────────────────────────────────────────────────
  Rule: Gemini direct extract — 不使用 yt-dlp / Whisper
  # ──────────────────────────────────────────────────────────────────────────

  @backend
  Scenario: YouTube 提交走 Gemini path，不依賴 yt-dlp 與 openai.Audio
    When 使用者 "pro_user@example.com" 提交 YouTube URL "https://www.youtube.com/watch?v=abc123"，科目為 1
    Then 操作成功
    And YouTube 擷取器不匯入 yt_dlp 模組
    And YouTube 擷取器不匯入 openai whisper 模組

  # ──────────────────────────────────────────────────────────────────────────
  Rule: 30 分鐘長度上限
  # ──────────────────────────────────────────────────────────────────────────

  @backend
  Scenario: 超過 30 分鐘的 YouTube 影片被拒絕，回 422
    When 使用者 "pro_user@example.com" 提交超過 30 分鐘的 YouTube URL，科目為 1
    Then 操作失敗，狀態碼為 422
    And 錯誤訊息應包含 "不可超過 30 分鐘"

  # ──────────────────────────────────────────────────────────────────────────
  Rule: YouTube 配額消耗 2 份
  # ──────────────────────────────────────────────────────────────────────────

  @backend
  Scenario: PRO 用戶上傳 YouTube URL 消耗 2 份配額
    Given 使用者 "pro_user@example.com" 本月已完成 0 次 LLM 資源解析
    When 使用者 "pro_user@example.com" 提交 YouTube URL "https://www.youtube.com/watch?v=abc123"，科目為 1
    Then 操作成功
    And 使用者 "pro_user@example.com" 本月 YouTube 配額已消耗 2 份

  @backend
  Scenario: PRO 用戶剩餘 1 份配額，上傳 YouTube 失敗（需 2 份）
    Given 使用者 "pro_user@example.com" 本月已完成 49 次 LLM 資源解析
    When 使用者 "pro_user@example.com" 提交 YouTube URL "https://www.youtube.com/watch?v=abc123"，科目為 1
    Then 操作失敗，狀態碼為 402
    And 錯誤訊息應包含 "配額"

  @backend
  Scenario: 上傳失敗（EnqueueFailedError）時 2 份配額退回
    Given 使用者 "pro_user@example.com" 本月已完成 0 次 LLM 資源解析
    When 使用者 "pro_user@example.com" 提交 YouTube URL 但背景排程失敗，科目為 1
    Then 操作失敗，狀態碼為 503
    And 使用者 "pro_user@example.com" 本月 YouTube 配額已退回 2 份
