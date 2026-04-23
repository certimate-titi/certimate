@ignore @query
Feature: 知識地圖 Canvas 三層 Zoom（PRD-046）

  三層 zoom 視覺化取代一次展開整棵樹的設計：
  - Tier 1 領域層（depth=0）：回傳 6-10 節點 + 子樹聚合掌握度
  - Tier 2/3：透過 children/{parent_id} 下鑽取得子節點

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案      |
      | 1        | free@example.com   | FREE          |
      | 2        | stu@example.com    | PRO_PLUS_399  |
    And 系統中有以下備考科目：
      | 科目 ID | 名稱      |
      | s1      | AI 基礎   |
    And 使用者 "stu@example.com" 備考 "AI 基礎"
    And 科目 "AI 基礎" 下有三層知識樹：
      | 節點 ID | 名稱             | depth | 父節點 |
      | d1     | 機器學習基礎      | 0     | null  |
      | t1     | 監督式學習        | 1     | d1    |
      | n1     | 線性迴歸          | 2     | t1    |
      | n2     | 邏輯迴歸          | 2     | t1    |
    And 使用者 "stu@example.com" 對節點 "n1" 的 mastery_rate 為 80

  Rule: Tier 1 領域層聚合後代掌握度

    Example: 取得領域層節點與聚合掌握度
      When 使用者 "stu@example.com" 呼叫 GET /api/v1/subjects/s1/canvas
      Then 操作成功
      And 回應節點數為 1
      And 節點 "機器學習基礎" 的 depth 為 0
      And 節點 "機器學習基礎" 的 mastery_rate 聚合自後代（n1=80, n2=0 → avg=40）

  Rule: Tier 2/3 分層下鑽

    Example: 取得 d1 的子節點
      When 使用者 "stu@example.com" 呼叫 GET /api/v1/subjects/s1/canvas/children/d1
      Then 操作成功
      And 回應節點數為 1
      And 父節點資訊包含 parent_name="機器學習基礎" 與 parent_depth=0

    Example: 取得 t1 的葉節點
      When 使用者 "stu@example.com" 呼叫 GET /api/v1/subjects/s1/canvas/children/t1
      Then 操作成功
      And 回應節點數為 2
      And 節點 "線性迴歸" 的 has_children 為 false

  Rule: 權限驗證

    Example: 未加入備考科目應拒絕
      When 使用者 "free@example.com" 呼叫 GET /api/v1/subjects/s1/canvas
      Then 回應狀態碼 403
      And 錯誤訊息包含 "尚未加入此備考科目"

    Example: 跨科目查詢 parent 應拒絕
      Given 另有科目 "s2" 下節點 "x1"
      When 使用者 "stu@example.com" 呼叫 GET /api/v1/subjects/s1/canvas/children/x1
      Then 回應狀態碼 404
      And 錯誤訊息包含 "父節點不存在或不屬於此科目"

  Rule: 空態區分

    Example: 科目無節點應標記 empty_reason
      Given 科目 "s1" 下所有節點被刪除
      When 使用者 "stu@example.com" 呼叫 GET /api/v1/subjects/s1/canvas
      Then 操作成功
      And 回應 empty_reason 為 "no_nodes_generated"
