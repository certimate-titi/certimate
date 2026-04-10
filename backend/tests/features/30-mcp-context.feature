# language: zh-TW
功能: MCP Context Server — 構建用戶學習上下文
  作為 AI Coach
  我想 獲取用戶的完整學習上下文
  以便 提供個性化的指導建議

  背景:
    假設 資料庫已清空
    且 用戶 "alice@example.com" 存在，密碼 "password123"
    且 用戶 "bob@example.com" 存在，密碼 "password123"

  場景: 構建用戶的完整學習上下文
    假設 用戶 "alice@example.com" 有知識節點 "IAM 身分管理" 及關聯 3 道題目
    且 用戶 "alice@example.com" 在知識節點 "IAM 身分管理" 上答錯 2 次
    且 用戶 "alice@example.com" 有知識節點 "VPC 網路設計" 及關聯 2 道題目
    且 用戶 "alice@example.com" 在知識節點 "VPC 網路設計" 上答錯 1 次
    當 MCP Context Server 構建 "alice@example.com" 的學習上下文
    那麼 回應狀態為 "success"
    且 回應包含弱點領域 "IAM 身分管理"
    且 回應包含 "alice@example.com" 的顯示名稱

  場景: 獲取特定弱點領域的詳細錯誤模式
    假設 用戶 "alice@example.com" 有知識節點 "IAM 身分管理"
    且 用戶 "alice@example.com" 在該知識節點上有 3 筆錯誤記錄
    當 MCP Context Server 獲取 "alice@example.com" 在 "IAM 身分管理" 的弱點詳情
    那麼 回應狀態為 "success"
    且 回應包含 3 筆錯誤記錄
    且 回應包含錯誤模式分析

  場景: 獲取用戶學習風格
    假設 用戶 "alice@example.com" 的學習風格為 "visual"
    當 MCP Context Server 獲取 "alice@example.com" 的學習風格
    那麼 回應狀態為 "success"
    且 回應包含視覺學習偏好分數
    且 回應包含最優間隔複習天數

  場景: 獲取用戶最近的錯誤記錄
    假設 用戶 "alice@example.com" 在過去 7 天內有 5 筆錯誤記錄
    當 MCP Context Server 獲取 "alice@example.com" 最近 10 筆錯誤
    那麼 回應狀態為 "success"
    且 回應包含 5 筆錯誤記錄
    且 每筆記錄包含題目 ID、知識點、答題時間

  場景: 用戶不存在時的錯誤處理
    當 MCP Context Server 構建 "nonexistent@example.com" 的學習上下文
    那麼 回應狀態為 "error"
    且 回應包含錯誤訊息 "User not found"
