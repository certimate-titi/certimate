@analytics
Feature: 前端事件接收端點（PRD-046 US-07）

  前端 localStorage queue 定時 flush 到 /analytics/events，
  後端驗證批次大小、寫入 analytics_events 表。

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email            | 訂閱方案      |
      | 1        | a@example.com    | PRO_PLUS_399  |

  Rule: 成功寫入事件批次

    Example: 送出 2 個事件
      When 使用者 "a@example.com" 送出 Analytics 事件批次：
        | name            | ts            | props          |
        | canvas_view     | 1714000000000 | {"tier":1}     |
        | canvas_drill_down | 1714000001000 | {"tier":2}   |
      Then 操作成功
      And Analytics 回應 accepted 為 2

  Rule: 批次驗證

    Example: 空批次應失敗
      When 使用者 "a@example.com" 送出空 Analytics 批次
      Then 操作失敗，狀態碼為 422
