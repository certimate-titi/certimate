# language: zh-TW
@ignore
功能: MCP Recommendation Server — 智能問題推薦與間隔複習
  作為 排程引擎
  我想 獲得基於用戶掌握度的問題推薦
  以便 優化學習安排

  背景:
    假設 資料庫已清空
    假設 用戶已創建:
      | email             | password    |
      | alice@example.com | password123 |
      | bob@example.com   | password123 |

  場景: 推薦掌握度低的知識點的問題
    假設 用戶 "alice@example.com" 有知識節點 "IAM 身分管理" 及關聯 5 道題目
    且 用戶 "alice@example.com" 在該知識節點上掌握度為 0.3
    且 用戶 "alice@example.com" 有知識節點 "VPC 網路設計" 及關聯 5 道題目
    且 用戶 "alice@example.com" 在該知識節點上掌握度為 0.7
    當 MCP Recommendation Server 為 "alice@example.com" 推薦 5 道題目
    那麼 回應狀態為 "success"
    且 回應包含 5 道推薦題目
    且 推薦題目優先來自掌握度低的知識點
    且 每道題目包含推薦理由

  場景: 計算艾賓浩斯間隔複習時間
    假設 用戶 "alice@example.com" 在 2 天前答對題目 "Q1"
    且 題目 "Q1" 對應知識節點 "IAM 身分管理"
    當 MCP Recommendation Server 計算 "alice@example.com" 題目 "Q1" 的複習時間
    那麼 回應狀態為 "success"
    且 回應包含下次複習時間
    且 下次複習距今天數大於 1 天

  場景: 建議學習路徑（包含前置知識）
    假設 知識節點樹狀結構：
      | 父節點 | 子節點 |
      | 基礎概念 | IAM 身分管理 |
      | IAM 身分管理 | IAM Role |
    當 MCP Recommendation Server 為 "alice@example.com" 建議學習 "IAM Role" 的路徑
    那麼 回應狀態為 "success"
    且 回應包含前置知識 "基礎概念"、"IAM 身分管理"
    且 回應包含推薦學習順序
    且 回應包含估計學習時間

  場景: 驗證知識節點的質量
    假設 知識節點資料：
      {
        "name": "IAM 身分管理",
        "definition": "身分識別與存取管理的核心概念...",
        "examples": ["例子1", "例子2"],
        "relationships": [
          {"concept": "授權", "relation_type": "前置知識"},
          {"concept": "策略", "relation_type": "相關概念"}
        ]
      }
    當 MCP Recommendation Server 驗證該節點質量
    那麼 回應狀態為 "success"
    且 節點質量驗證通過
    且 質量分數大於等於 0.6

  場景: 節點質量驗證失敗——定義不足
    假設 知識節點資料不含 definition 字段
    當 MCP Recommendation Server 驗證該節點質量
    那麼 回應狀態為 "success"
    且 節點質量驗證失敗
    且 回應包含問題 "缺少 definition 字段"

  場景: 為未答過的題目計算複習時間
    假設 用戶 "alice@example.com" 從未答過題目 "Q2"
    當 MCP Recommendation Server 計算 "alice@example.com" 題目 "Q2" 的複習時間
    那麼 回應狀態為 "success"
    且 下次複習時間距今 1 天
    且 重複次數為 0
