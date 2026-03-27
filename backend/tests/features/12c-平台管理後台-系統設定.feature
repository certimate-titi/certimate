@command
Feature: 平台管理後台 — 系統設定（僅 super_admin）

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                   | 訂閱方案 | 角色        |
      | 1        | super@certimate.com     | ULTRA    | SUPER_ADMIN |
      | 2        | ops@certimate.com       | ULTRA    | ADMIN       |
    And 系統中有以下 AI 模型路由設定：
      | 方案  | 任務類型 | 主要模型          | 備援模型         |
      | FREE  | basic    | gemini-1.5-flash  | llama-3.1-8b    |
      | PRO   | advanced | claude-3.5-sonnet | gemini-1.5-flash |
    And 系統中有以下方案限額設定：
      | 方案  | 每月上傳數 | 每月考試數 | 每日 AI 對話數 | 每月 Vision 頁數 |
      | FREE  | 5          | 10         | 3              | 0                |
      | PRO   | 50         | 100        | 30             | 0                |
    And 系統中有以下 Feature Flag：
      | Flag ID | Flag Key                 | 狀態  | 上線比例 |
      | 1       | enable_socratic_tutor_v2 | false | 0        |

  # ========== AI 模型路由 ==========

  Rule: 後置（狀態）- 更新 AI 模型路由應即時生效並記錄審計日誌

    Example: super_admin 變更 FREE 方案的基本模型成功
      When 使用者 "super@certimate.com" 更新 AI 模型路由，方案為 "FREE"，任務類型為 "basic"，主要模型為 "llama-3.1-8b"
      Then 操作成功
      And FREE 方案 basic 任務的主要模型應為 "llama-3.1-8b"
      And 系統應記錄審計日誌：
        | 欄位    | 值                                          |
        | action  | update_model_routing                        |
        | details | FREE basic: gemini-1.5-flash → llama-3.1-8b |

  # ========== 方案限額 ==========

  Rule: 後置（狀態）- 更新方案限額應即時生效

    Example: super_admin 調整 FREE 方案每月上傳數成功
      When 使用者 "super@certimate.com" 更新方案限額，方案為 "FREE"，每月上傳數為 8
      Then 操作成功
      And FREE 方案的每月上傳數限額應為 8

  # ========== 系統公告 ==========

  Rule: 前置（參數）- 建立公告必須提供標題與內容

    Scenario Outline: 建立公告缺少 <缺少參數> 時失敗
      When 使用者 "super@certimate.com" 建立系統公告，標題為 <標題>，內容為 <內容>，類型為 "info"
      Then 操作失敗，錯誤為「必要參數未提供」

      Examples:
        | 缺少參數 | 標題         | 內容              |
        | 標題     |              | 2026/04/01 維護   |
        | 內容     | 系統維護通知  |                   |

  Rule: 後置（狀態）- 成功建立公告後應在指定時間範圍內顯示

    Example: 建立排程系統維護公告成功
      When 使用者 "super@certimate.com" 建立系統公告：
        | 欄位         | 值                          |
        | title        | 系統維護通知                 |
        | content      | 2026/04/01 02:00-06:00 維護  |
        | type         | maintenance                  |
        | display_mode | banner                       |
        | starts_at    | 2026-03-30T00:00:00          |
        | ends_at      | 2026-04-01T06:00:00          |
      Then 操作成功
      And 公告狀態應為 "active"

  # ========== Feature Flag ==========

  Rule: 後置（狀態）- 更新 Feature Flag 上線比例應即時生效

    Example: 設定 Feature Flag 20% 漸進式上線成功
      When 使用者 "super@certimate.com" 更新 Feature Flag 1，上線比例為 20，目標方案為 "PRO,PRO_PLUS"
      Then 操作成功
      And Feature Flag "enable_socratic_tutor_v2" 應為啟用狀態
      And 上線比例應為 20

  # ========== 審計日誌 ==========

  Rule: 後置（回應）- 審計日誌應回傳不可變的完整操作紀錄

    Example: 查看審計日誌取得完整操作紀錄
      When 使用者 "super@certimate.com" 查看審計日誌
      Then 操作成功
      And 回應中每筆紀錄應包含審計日誌欄位
