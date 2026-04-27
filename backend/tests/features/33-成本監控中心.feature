@backend @cost_monitor
Feature: 雲端與 AI 成本監控中心

  說明：Super Admin 專屬的成本可視化與預算告警中心。
  整合 Anthropic Admin API、Gemini / Voyage 應用層 token tracking、
  GCP BigQuery Billing Export，提供即時用量、趨勢與多層級預算告警。
  一般 admin 不可見此頁面。

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                 | 訂閱方案    | 角色         |
      | 1        | super@certimate.com   | ULTRA_1599 | super_admin  |
      | 2        | ops@certimate.com     | ULTRA_1599 | admin        |
      | 3        | user@certimate.com    | PRO_199    | user         |
    And 系統中有以下預算設定：
      | scope         | monthly_limit_usd | warning_percent | degrade_percent | disable_percent |
      | AI_ANTHROPIC  | 500               | 50              | 80              | 100             |
      | AI_GEMINI     | 300               | 50              | 80              | 100             |
      | AI_VOYAGE     | 50                | 50              | 80              | 100             |
      | GCP_TOTAL     | 2000              | 50              | 80              | 100             |
    And 當月累計用量為：
      | scope        | current_usd |
      | AI_ANTHROPIC | 120.50      |
      | AI_GEMINI    | 85.20       |
      | AI_VOYAGE    | 10.00       |
      | GCP_TOTAL    | 450.75      |

  # ========== 權限隔離 ==========

  Rule: 前置 - 僅 super_admin 可存取成本監控 API

    Example: super_admin 成功取得當月成本總覽
      When 使用者 "super@certimate.com" 查看成本監控總覽
      Then 操作成功
      And 回應應包含各 scope 的當月金額：
        | scope        | current_usd | limit_usd | percent |
        | AI_ANTHROPIC | 120.50      | 500       | 24.10   |
        | AI_GEMINI    | 85.20       | 300       | 28.40   |
        | AI_VOYAGE    | 42.00       | 150       | 28.00   |
        | GCP_TOTAL    | 450.75      | 2000      | 22.54   |

    Example: 一般 admin 存取被拒絕
      When 使用者 "ops@certimate.com" 查看成本監控總覽
      Then 操作失敗
      And 錯誤代碼為 "FORBIDDEN_SUPER_ADMIN_ONLY"

    Example: 一般 user 存取被拒絕
      When 使用者 "user@certimate.com" 查看成本監控總覽
      Then 操作失敗
      And 錯誤代碼為 "FORBIDDEN_SUPER_ADMIN_ONLY"

  # ========== 單一供應商詳情 ==========

  Rule: 後置（回應）- 供應商詳情應回傳 token 級明細與趨勢

    Example: 查看 Anthropic 用量詳情
      When 使用者 "super@certimate.com" 查看供應商 "anthropic" 用量詳情
      Then 操作成功
      And 回應應包含欄位 "provider" 為 "anthropic"
      And 回應應包含欄位 "input_tokens_total"
      And 回應應包含欄位 "output_tokens_total"
      And 回應應包含欄位 "cost_usd"
      And 回應應包含 30 天的 daily_series 趨勢資料

    Example: 查看 Voyage 用量詳情包含配額鎖狀態
      When 使用者 "super@certimate.com" 查看供應商 "voyage" 用量詳情
      Then 操作成功
      And 回應應包含欄位 "quota_lock_enabled" 為 true
      And 回應應包含欄位 "quota_remaining_usd"

  # ========== GCP 服務分類 ==========

  Rule: 後置（回應）- GCP 帳單應依服務分類呈現且快取 1 小時

    Example: 查看 GCP 服務分類
      Given BigQuery Billing Export 有以下資料：
        | service              | cost_usd | billing_date |
        | Cloud Run            | 120.00   | 2026-04-01   |
        | Firebase Hosting     | 25.50    | 2026-04-01   |
        | Cloud SQL            | 180.25   | 2026-04-01   |
        | Gemini API           | 85.20    | 2026-04-01   |
        | Cloud Storage        | 15.00    | 2026-04-01   |
        | Logging              | 25.00    | 2026-04-01   |
      When 使用者 "super@certimate.com" 查看 GCP 服務分類
      Then 操作成功
      And 回應應包含各服務金額降冪排列
      And 回應應包含欄位 "cached_at"
      And 回應應包含欄位 "total_usd" 為 450.95

  # ========== 預算門檻告警 ==========

  Rule: 後置（狀態）- 達 50% 應觸發警告但不降級

    Example: Anthropic 達 50% 觸發警告
      Given 當月 Anthropic 累計用量為 250 USD
      When 系統執行預算檢查
      Then 應寫入 budget_alert_log 記錄一筆 "WARNING" 告警
      And 應發送 Email 至 "super@certimate.com"
      And 應建立站內通知
      And AI 功能狀態應為 "active"

  Rule: 後置（狀態）- 達 80% 應觸發降級並停止新 AI 生成

    Example: Gemini 達 80% 觸發降級
      Given 當月 Gemini 累計用量為 240 USD
      When 系統執行預算檢查
      Then 應寫入 budget_alert_log 記錄一筆 "DEGRADE" 告警
      And AI 功能狀態應為 "degraded"
      And 使用者 "user@certimate.com" 嘗試生成新考題時應被拒絕
      And 錯誤代碼為 "AI_BUDGET_DEGRADED"
      And 使用者 "user@certimate.com" 仍可瀏覽既有的 AI 生成內容

  Rule: 後置（狀態）- 達 100% 應硬性停用 AI 功能

    Example: Voyage 達 100% 觸發硬性停用
      Given 當月 Voyage 累計用量為 150 USD
      When 系統執行預算檢查
      Then 應寫入 budget_alert_log 記錄一筆 "DISABLED" 告警
      And AI 功能狀態應為 "disabled"
      And 使用者 "user@certimate.com" 上傳新資源生成心智圖時應被拒絕
      And 錯誤代碼為 "AI_BUDGET_EXHAUSTED"

  Rule: 前置 - GCP 預算僅告警不可自動降級

    Example: GCP 達 80% 僅告警不影響功能
      Given 當月 GCP 累計用量為 1600 USD
      When 系統執行預算檢查
      Then 應寫入 budget_alert_log 記錄一筆 "WARNING" 告警
      And 應發送 Email 至 "super@certimate.com"
      And AI 功能狀態應為 "active"

  # ========== Voyage 配額鎖與降級佇列 ==========

  Rule: 前置 - 呼叫 Voyage embedding 前必須通過配額鎖檢查

    Example: 配額足夠允許呼叫
      Given 當月 Voyage 累計用量為 20 USD
      And 本次 embedding 預估成本為 0.15 USD
      When 系統呼叫 voyage_quota_service.check_and_reserve
      Then 操作成功
      And 應預扣 0.15 USD 至保留額度

    Example: 配額達 80% 降級門檻新資源進入等待佇列
      Given 當月 Voyage 累計用量為 40 USD
      And AI_VOYAGE 的 degrade_percent 為 80
      When 使用者 "user@certimate.com" 上傳新資源
      Then 操作成功
      And 該資源狀態應為 "PENDING_BUDGET_RECOVERY"
      And 系統不應呼叫 Voyage API 為此資源 embed
      And 使用者應收到站內通知「AI 資源處理已排隊，因本月 embedding 預算已達降級門檻」

    Example: 既有資源查詢不受降級影響
      Given 當月 Voyage 累計用量為 40 USD
      And 既有知識心智圖已完成 embedding
      When 使用者 "user@certimate.com" 查詢既有心智圖
      Then 操作成功
      And 查詢應走 Voyage 向量庫正常回傳結果

    Example: 配額達 100% 硬性停用門檻
      Given 當月 Voyage 累計用量為 50 USD
      And 本次 embedding 預估成本為 0.50 USD
      When 系統呼叫 voyage_quota_service.check_and_reserve
      Then 操作失敗
      And 錯誤代碼為 "VOYAGE_QUOTA_EXCEEDED"

  Rule: 後置（狀態）- 擴充預算後佇列應自動恢復處理

    Example: Super Admin 擴充預算後 pending 資源恢復處理
      Given 有 3 筆資源狀態為 "PENDING_BUDGET_RECOVERY"
      And AI_VOYAGE 月預算為 50 USD 且當月已用 42 USD
      When 使用者 "super@certimate.com" 將 "AI_VOYAGE" 月預算修改為 100 USD，原因為 "臨時擴充預算恢復佇列"
      Then 操作成功
      And 3 筆等待中的資源應在 1 分鐘內重新進入 processing 狀態
      And 每筆資源 embed 完成後狀態應轉為 "COMPLETED"

  # ========== 預算設定管理 ==========

  Rule: 後置（狀態）- 修改預算需寫入稽核日誌

    Example: super_admin 修改 Anthropic 月預算
      When 使用者 "super@certimate.com" 將 "AI_ANTHROPIC" 月預算修改為 600 USD，原因為 "業務成長"
      Then 操作成功
      And budget_config 中 "AI_ANTHROPIC" 的 monthly_limit_usd 應為 600
      And admin_audit_log 應有一筆 "BUDGET_UPDATED" 記錄
      And 稽核記錄的 actor 應為 "super@certimate.com"
      And 稽核記錄應包含原因 "業務成長"

    Example: 一般 admin 修改預算被拒絕
      When 使用者 "ops@certimate.com" 將 "AI_ANTHROPIC" 月預算修改為 600 USD
      Then 操作失敗
      And 錯誤代碼為 "FORBIDDEN_SUPER_ADMIN_ONLY"

  Rule: 後置（狀態）- 整體調整應依現有比例自動分配至各 scope

    Example: 整體預算加 20% 自動等比分配
      Given 當前預算設定為：
        | scope        | monthly_limit_usd |
        | AI_ANTHROPIC | 700               |
        | AI_GEMINI    | 100               |
        | AI_VOYAGE    | 50                |
        | GCP_TOTAL    | 400               |
      When 使用者 "super@certimate.com" 執行整體調整 "+20%"，原因為 "Q2 業務擴張"
      Then 操作成功
      And budget_config 應更新為：
        | scope        | monthly_limit_usd |
        | AI_ANTHROPIC | 840               |
        | AI_GEMINI    | 120               |
        | AI_VOYAGE    | 60                |
        | GCP_TOTAL    | 480               |
      And admin_audit_log 應有一筆 "BUDGET_GLOBAL_SCALED" 記錄
      And 稽核記錄應包含 scale_factor 為 1.20
      And 稽核記錄應包含 before 與 after 的完整快照

    Example: 整體預算設為固定金額等比分配
      Given 當前預算設定為：
        | scope        | monthly_limit_usd |
        | AI_ANTHROPIC | 700               |
        | AI_GEMINI    | 100               |
        | AI_VOYAGE    | 50                |
        | GCP_TOTAL    | 400               |
      When 使用者 "super@certimate.com" 執行整體調整設為 1500 USD，原因為 "季度預算縮減"
      Then 操作成功
      And budget_config 的 monthly_limit_usd 總和應為 1500
      And 各 scope 應依原比例重新分配（誤差 ≤ 1 USD，四捨五入至整數）
      And admin_audit_log 應有一筆 "BUDGET_GLOBAL_SET" 記錄

    Example: 整體調整後 Super Admin 可再個別微調
      Given 當前預算設定為：
        | scope        | monthly_limit_usd |
        | AI_ANTHROPIC | 840               |
        | AI_GEMINI    | 120               |
        | AI_VOYAGE    | 60                |
        | GCP_TOTAL    | 480               |
      When 使用者 "super@certimate.com" 將 "AI_VOYAGE" 月預算修改為 80 USD，原因為 "Voyage 需更多緩衝"
      Then 操作成功
      And budget_config 中 "AI_VOYAGE" 的 monthly_limit_usd 應為 80
      And 其他 scope 不受影響

    Example: 一般 admin 執行整體調整被拒絕
      When 使用者 "ops@certimate.com" 執行整體調整 "+20%"
      Then 操作失敗
      And 錯誤代碼為 "FORBIDDEN_SUPER_ADMIN_ONLY"

    Example: 整體調整比例超出合理範圍應拒絕
      When 使用者 "super@certimate.com" 執行整體調整 "+500%"
      Then 操作失敗
      And 錯誤代碼為 "BUDGET_SCALE_OUT_OF_RANGE"
      And 錯誤訊息應提示「整體調整範圍須介於 -50% 至 +200% 之間」

  Rule: 後置（狀態）- 手動解除停用需二次確認與原因

    Example: super_admin 解除 Voyage 停用狀態
      Given AI 功能狀態為 "disabled"
      When 使用者 "super@certimate.com" 手動解除停用 "AI_VOYAGE"，原因為 "已臨時擴充預算"
      Then 操作成功
      And AI 功能狀態應為 "active"
      And admin_audit_log 應有一筆 "BUDGET_OVERRIDE" 記錄

  # ========== GCP Native Budget 單向同步 ==========

  Rule: 後置（狀態）- AI_GEMINI / GCP_TOTAL 預算變更應同步建立或更新 GCP Native Budget

    Example: 首次設定 AI_GEMINI 預算應自動建立 GCP Budget
      Given budget_config 中 "AI_GEMINI" 的 gcp_budget_resource_name 為 null
      When 使用者 "super@certimate.com" 將 "AI_GEMINI" 月預算修改為 100 USD
      Then 操作成功
      And 系統應透過 billingbudgets.googleapis.com 建立對應 GCP Budget
      And budget_config 中 "AI_GEMINI" 的 gcp_budget_resource_name 應被設定
      And GCP Budget 的 filter 應限定於 service "generativelanguage.googleapis.com"
      And GCP Budget 的金額應為 100 USD
      And GCP Budget 的三級門檻應為 50% / 80% / 100%
      And admin_audit_log 應有一筆 "BUDGET_UPDATED" 記錄
      And admin_audit_log details 應包含 "gcp_sync": "created"

    Example: 更新既有 GCP_TOTAL 預算應更新對應 GCP Budget
      Given budget_config 中 "GCP_TOTAL" 已有 gcp_budget_resource_name
      When 使用者 "super@certimate.com" 將 "GCP_TOTAL" 月預算修改為 500 USD
      Then 操作成功
      And 系統應呼叫 GCP Budgets API 更新既有 Budget
      And admin_audit_log details 應包含 "gcp_sync": "updated"

    Example: AI_ANTHROPIC 與 AI_VOYAGE 預算變更不觸發 GCP 同步
      When 使用者 "super@certimate.com" 將 "AI_ANTHROPIC" 月預算修改為 800 USD
      Then 操作成功
      And 系統不應呼叫 billingbudgets.googleapis.com
      And admin_audit_log details 的 "gcp_sync" 欄位應為 "skipped_non_gcp"

  Rule: 前置 - GCP Budget 同步失敗不應阻擋主流程

    Example: GCP Budgets API 呼叫失敗但本地更新成功
      Given budget_config 中 "AI_GEMINI" 尚未同步
      And GCP Budgets API 暫時無法回應
      When 使用者 "super@certimate.com" 將 "AI_GEMINI" 月預算修改為 100 USD
      Then 操作成功
      And budget_config 中 "AI_GEMINI" 的 monthly_limit_usd 應為 100
      And admin_audit_log details 應包含 "gcp_sync": "failed"
      And 回應應包含警告訊息「GCP Native Budget 同步失敗，本地預算已更新」

  Rule: 後置（狀態）- 整體調整也應同步 AI_GEMINI 與 GCP_TOTAL 的 GCP Budget

    Example: 整體調整 +20% 後 GCP 可同步 scope 也應等比更新
      Given budget_config 各 scope 已有 gcp_budget_resource_name
      When 使用者 "super@certimate.com" 執行整體調整 "+20%"，原因為 "擴張測試"
      Then 操作成功
      And AI_GEMINI 與 GCP_TOTAL 對應的 GCP Budget 金額應被更新為原金額的 1.20 倍
      And AI_ANTHROPIC 與 AI_VOYAGE 不觸發 GCP 同步

  # ========== 趨勢圖 ==========

  Rule: 後置（回應）- 趨勢圖應回傳最近 30 天每日成本資料

    Example: 查看成本趨勢
      When 使用者 "super@certimate.com" 查看成本趨勢圖，範圍為最近 30 天
      Then 操作成功
      And 回應應包含 30 個每日資料點
      And 每個資料點應包含 "date"、"ai_anthropic"、"ai_gemini"、"ai_voyage"、"gcp_total" 欄位
