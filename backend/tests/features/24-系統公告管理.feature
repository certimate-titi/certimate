@command
Feature: 系統公告管理

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案     | 角色         |
      | 1        | admin@example.com  | ULTRA_1599   | SUPER_ADMIN  |
      | 2        | user@example.com   | PRO_199      | USER         |

  # ========== 公告 CRUD ==========

  Rule: 命令（管理）- 管理員可建立系統公告

    Example: 建立一則系統公告
      When 管理員 "admin@example.com" 建立系統公告：
        | 欄位       | 值                         |
        | title      | 系統維護通知                 |
        | content    | 預計於 04/10 進行系統維護     |
        | type       | info                       |
        | is_active  | true                       |
      Then 操作應成功
      And 系統中應存在公告 "系統維護通知"

    Example: 一般使用者無法建立公告
      When 使用者 "user@example.com" 建立系統公告：
        | 欄位   | 值       |
        | title  | 測試公告  |
      Then 操作應失敗，錯誤訊息為 "權限不足"

  # ========== 公告查詢 ==========

  Rule: 查詢 - 使用者可查看啟用中的公告

    Example: 查詢啟用中的公告列表
      Given 系統中有以下公告：
        | 公告 ID | 標題       | 類型 | 啟用 |
        | 1       | 新功能上線  | info | true |
        | 2       | 已過期公告  | warn | false|
      When 使用者 "user@example.com" 查詢啟用中的公告
      Then 操作應成功
      And API 回應應包含 1 則公告
      And 公告標題應為 "新功能上線"

  # ========== 公告停用 ==========

  Rule: 命令（管理）- 管理員可停用公告

    Example: 停用一則公告
      Given 系統中有啟用的公告 "系統維護通知"
      When 管理員 "admin@example.com" 停用公告 "系統維護通知"
      Then 操作應成功
      And 公告 "系統維護通知" 的 is_active 應為 false
