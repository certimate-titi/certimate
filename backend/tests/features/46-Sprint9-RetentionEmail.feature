# language: zh-TW
@feature_46 @retention_email @sprint_9 @backend
Feature: Email retention 觸發系統（議題 E）
  覆蓋 Sprint 9 議題 E — 4 封 retention email：
  - 每日複習提醒（trigger_daily_review）
  - 週報摘要（trigger_weekly_report）
  - 連勝即將斷氣（trigger_streak_warning）
  - 上傳解析失敗（trigger_parse_failure）

  完整文案見 docs/ops/retention-email-templates-2026-05-09.md

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"，user_email_preferences 全開
    And 已存在 FREE 用戶 "bob@example.com"，user_email_preferences 全開
    And 已存在 SUPER_ADMIN 用戶 "admin@certimate.com"

  @backend
  Rule: user_email_preferences schema 與預設值
    Scenario: 新用戶自動建立 preferences row（全開為預設，但 FREE 不收行銷信）
      Given alice 剛註冊
      Then user_email_preferences 含 alice 一行
      And daily_review_enabled = true
      And weekly_report_enabled = true
      And streak_warning_enabled = true
      And parse_failure_enabled = true（事務型必開，無法關）
      And unsubscribe_token 為 32+ 字元 JWT

    Scenario: FREE 用戶不會收到「行銷型」信
      Given bob 是 FREE 方案，user_email_preferences daily_review_enabled = true
      When EmailService.send_daily_review(bob)
      Then 不寄送，回傳 skipped: "FREE_NOT_ELIGIBLE"

    Scenario: 解析失敗 email 即使用戶 opt-out 也必寄（事務型）
      Given alice 設 parse_failure_enabled = false（API 應拒絕，但 DB 直改可能繞過）
      When resource_parse_jobs.status = 'FAILED' 觸發
      Then 仍寄送 send_parse_failure(alice)
      And email_send_log 含此筆（log_type = "TRANSACTIONAL"）

  @backend
  Rule: 每日複習提醒（trigger_daily_review，每日 08:00 TW）
    Scenario: 用戶有 due 鷹架 → 寄送
      Given alice 有 5 個 scaffold_review_schedule.due_date <= today
      When admin POST /admin/retention/run-daily-cron?trigger=daily_review
      Then alice 收到 1 封信，subject 含「5 個重點」
      And email_send_log 含 trigger_id = "daily_review"
      And CTA 連結為 ${FRONTEND_URL}/today

    Scenario: 用戶無 due 鷹架 → 不寄
      Given alice 有 0 個 due 鷹架
      When admin POST /admin/retention/run-daily-cron?trigger=daily_review
      Then alice 不在收件清單

    Scenario: 24 小時內已寄過同類信不重寄
      Given alice 今天已收過 daily_review email
      When admin 再次 POST /admin/retention/run-daily-cron?trigger=daily_review
      Then alice 不在收件清單，原因 "ALREADY_SENT_TODAY"

  @backend
  Rule: 連勝警告（trigger_streak_warning，每日 22:00 TW）
    Scenario: 連勝 ≥ 3 天且當日未登入 → 寄送
      Given alice 連勝 5 天，今天 22:00 前最後登入時間為昨天
      When admin POST /admin/retention/run-daily-cron?trigger=streak_warning
      Then alice 收到信，subject 含「5 天連勝」

    Scenario: 連勝 < 3 天 → 不寄（避免騷擾新用戶）
      Given alice 連勝 2 天，今天未登入
      Then alice 不在收件清單

    Scenario: 用戶今天已登入 → 不寄
      Given alice 連勝 5 天，今天已有 last_login_at
      Then alice 不在收件清單

  @backend
  Rule: 週報（trigger_weekly_report，週日 09:00 TW，FREE 不收）
    Scenario: PRO 用戶 weekly_reports 寫入後寄送
      Given alice 為 PRO，weekly_reports 表昨天新增一行 user_id=alice
      When admin POST /admin/retention/run-daily-cron?trigger=weekly_report
      Then alice 收到信，subject 含「本週」

    Scenario: FREE 用戶不寄送週報（升級誘因）
      Given bob 為 FREE，weekly_reports 表有他的紀錄
      Then bob 不在收件清單，原因 "FREE_NOT_ELIGIBLE"

  @backend
  Rule: 解析失敗（trigger_parse_failure，即時，所有方案）
    Scenario: parse job FAILED 後 5 分鐘內觸發寄送
      Given alice 上傳檔案，resource_parse_jobs.status 變為 FAILED with failure_reason = "PDF 加密無法讀取"
      When 觸發 send_parse_failure(alice, resource_id, failure_reason)
      Then alice 收到信，subject 含「上傳失敗」
      And 內文含 failure_reason 文字片段
      And CTA 連結為重新上傳 URL

  @backend
  Rule: Unsubscribe token JWT
    Scenario: 用戶點退訂連結 → 修改對應 preference flag
      Given alice 收到含 unsubscribe_token 的信
      When alice GET /api/v1/email/unsubscribe?token=${token}&trigger=daily_review
      Then 回 200，daily_review_enabled = false
      And alice 下次不會收到 daily_review

    Scenario: token 無效 → 拒絕
      When 任何人 GET /api/v1/email/unsubscribe?token=invalid_xxx
      Then 回 400，message = "退訂連結無效或已過期"

    Scenario: token purpose 不對 → 拒絕（防其他 token 誤用）
      When 用 password_reset 的 token 呼叫 unsubscribe
      Then 回 400

  @backend
  Rule: 寄送頻率與重複防護
    Scenario: email_send_log 記錄每次成功 / 失敗 / skipped
      Given admin POST /admin/retention/run-daily-cron?trigger=daily_review
      Then email_send_log 含 (user_id, trigger_id, status="sent"|"skipped"|"failed", reason)
      And 每筆有 sent_at timestamp

    Scenario: SMTP 失敗時記 failed 但不 retry（避免轟炸）
      Given SMTP 暫時不可用
      When 觸發 send_daily_review(alice)
      Then email_send_log 含 status="failed", error 內容
      And alice 不會被自動 retry（隔天才能再寄）

  @backend @permission
  Rule: 僅 SUPER_ADMIN 可手動觸發 cron
    Scenario: admin POST /admin/retention/run-daily-cron 回 200
      Then 回 200，summary 含 sent_count / skipped_count / failed_count

    Scenario: 一般用戶 POST /admin/retention/run-daily-cron 回 403
      When alice POST /admin/retention/run-daily-cron
      Then 回 403，message = "需要 SUPER_ADMIN 權限"
