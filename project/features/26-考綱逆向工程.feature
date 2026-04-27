Feature: 考綱逆向工程

  AI 分析考古題與教材，透過語意階層萃取（Semantic Hierarchy Extraction）
  自動還原考綱結構為知識心智圖。

  核心架構：
    第一階段：語意階層萃取（後端 AI Pipeline）
      - 輸入：考古題集合 / 教材 / 考綱文件
      - 處理：LLM 語意分析 → 核心主題 → 次要概念 → 細節證據
      - 輸出：結構化 JSON（巢狀 tree）+ Markdown（巢狀列表）

    第二階段：前端介面渲染（消費 JSON）
      - 母層級 → 中心節點
      - 子層級 → 展開分支
      - 支援展開/收合、節點點擊、匯出為 Markdown

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案       | 角色         |
      | 1        | admin@example.com  | ULTRA_1599     | SUPER_ADMIN  |
      | 2        | pro@example.com    | PRO_PLUS_399   | USER         |
      | 3        | free@example.com   | FREE           | USER         |
    And 系統中有以下考科分類：
      | 分類 ID | 名稱     |
      | 1       | 金融證照  |
    And 系統中有以下考科：
      | 考科 ID | 分類 ID | 名稱         | is_popular |
      | 1       | 1       | 信託業業務人員 | true       |

  # ========== 觸發逆向工程 ==========

  Rule: 命令（觸發）- 管理員可對考科題庫執行考綱逆向工程

    Example: 對已有考古題的考科啟動考綱逆向工程
      Given 考科 "信託業業務人員" 已匯入 180 題考古題
      When 管理員 "admin@example.com" 對考科 "信託業業務人員" 執行考綱逆向工程
      Then 操作成功
      And 系統應建立一筆逆向工程任務，狀態為 "PROCESSING"

    Example: 題庫不足時拒絕執行逆向工程
      Given 考科 "信託業業務人員" 僅有 5 題考古題
      When 管理員 "admin@example.com" 對考科 "信託業業務人員" 執行考綱逆向工程
      Then 操作失敗，錯誤為「題庫數量不足，至少需要 30 題才能進行考綱逆向工程」

    Example: 一般使用者無法執行考綱逆向工程
      When 使用者 "pro@example.com" 對考科 "信託業業務人員" 執行考綱逆向工程
      Then 操作失敗，錯誤為「僅管理員可執行此操作」

  # ========== 語意階層萃取（第一階段） ==========

  Rule: 後置（萃取）- AI 應從題目中萃取出多層級知識結構

    Example: 逆向工程完成後產出三層知識結構
      Given 考科 "信託業業務人員" 已匯入 180 題考古題
      And 管理員已對考科 "信託業業務人員" 啟動逆向工程且處理完成
      When 管理員 "admin@example.com" 查詢考科 "信託業業務人員" 的知識樹
      Then 操作成功
      And 知識樹應包含至少 3 層結構：
        | 層級 | 說明                   | 範例                           |
        | 1    | 核心主題（章）          | 信託法規、信託實務、信託稅制       |
        | 2    | 次要概念（節）          | 信託契約要素、受託人義務          |
        | 3    | 細節知識點（考點）      | 信託財產獨立性原則、忠實義務範圍   |
      And 每個知識節點應包含：
        | 欄位                    | 說明                         |
        | name                   | 節點名稱                      |
        | depth                  | 層級深度（1/2/3）             |
        | parent_id              | 父節點 ID（根節點為 null）     |
        | mapped_question_count  | 對應的考古題數量               |
        | exam_frequency         | 出題頻率（high/medium/low）    |

  Rule: 後置（結構化輸出）- 萃取結果應以 JSON 樹狀結構儲存

    Example: 知識樹 API 回應為巢狀 JSON 格式
      Given 考科 "信託業業務人員" 已完成考綱逆向工程
      When 管理員 "admin@example.com" 查詢考科 "信託業業務人員" 的知識樹
      Then 回應格式應為巢狀 JSON：
        | 欄位       | 型別           | 說明                    |
        | id        | string (uuid)  | 節點唯一識別              |
        | name      | string         | 節點名稱                 |
        | depth     | integer        | 層級深度                 |
        | children  | array          | 子節點陣列（遞迴結構）     |
        | metadata  | object         | 出題頻率、對應題數等統計    |

  # ========== Markdown 雙向轉換 ==========

  Rule: 後置（匯出）- 知識樹可匯出為 Markdown 巢狀列表格式

    Example: 將知識樹匯出為 Markdown
      Given 考科 "信託業業務人員" 已完成考綱逆向工程
      When 使用者 "pro@example.com" 匯出考科 "信託業業務人員" 的知識樹為 Markdown
      Then 操作成功
      And 回應 content_type 應為 "text/markdown"
      And 內容應為巢狀列表格式，例如：
        """
        # 信託法規
        ## 信託契約
        ### 信託契約要素
        ### 信託財產獨立性原則
        ## 受託人義務
        ### 忠實義務
        ### 善良管理人注意義務
        # 信託實務
        ## 金錢信託
        ## 有價證券信託
        # 信託稅制
        ## 信託課稅原則
        """

  Rule: 命令（匯入）- 管理員可匯入 Markdown 格式的知識結構覆寫現有知識樹

    Example: 匯入修改後的 Markdown 知識結構
      Given 考科 "信託業業務人員" 已完成考綱逆向工程
      When 管理員 "admin@example.com" 匯入以下 Markdown 知識結構到考科 "信託業業務人員"：
        """
        # 信託法規（修訂版）
        ## 信託契約
        ### 信託契約三要素
        ## 受託人義務與責任
        # 信託實務操作
        """
      Then 操作成功
      And 考科 "信託業業務人員" 的知識樹應更新為匯入的結構
      And 根節點數量應為 2（信託法規（修訂版）、信託實務操作）

  # ========== 題目與節點映射 ==========

  Rule: 後置（映射）- 逆向工程應自動將考古題映射到對應知識節點

    Example: 考古題自動歸類到萃取出的知識節點
      Given 考科 "信託業業務人員" 已完成考綱逆向工程
      When 管理員 "admin@example.com" 查詢知識節點 "信託財產獨立性原則" 的題目統計
      Then 操作成功
      And 回應應包含：
        | 欄位                   | 說明                    |
        | node_name             | 信託財產獨立性原則        |
        | mapped_question_count | 對應的考古題數量（> 0）   |
        | bloom_distribution    | Bloom 分類分佈           |
        | exam_frequency        | 出題頻率等級             |

    Example: 未被映射的考古題應標記為待分類
      Given 考科 "信託業業務人員" 已完成考綱逆向工程
      When 管理員 "admin@example.com" 查詢未映射題目清單
      Then 回應中 unmapped_questions 應為 0 或接近 0
      And 若有未映射題目，每題應包含 suggested_node（AI 建議歸屬節點）

  # ========== 品質驗證 ==========

  Rule: 後置（品質）- 逆向工程結果應通過品質檢查

    Example: 知識樹覆蓋率應達標
      Given 考科 "信託業業務人員" 已完成考綱逆向工程（180 題）
      When 管理員 "admin@example.com" 查詢逆向工程品質報告
      Then 操作成功
      And 回應應包含：
        | 欄位                | 說明                            |
        | coverage_rate      | 題目覆蓋率（已映射題數/總題數）    |
        | node_count         | 知識節點總數                     |
        | max_depth          | 最大層級深度                     |
        | orphan_node_count  | 無題目對應的孤立節點數            |
        | reliability        | 信度等級（green/yellow/red）     |
      And coverage_rate 應大於等於 90%
      And max_depth 應介於 3 至 5 之間

    Example: 節點數過少時標記為低信度
      Given 考科 "信託業業務人員" 僅有 35 題考古題
      And 管理員已對考科 "信託業業務人員" 啟動逆向工程且處理完成
      When 管理員 "admin@example.com" 查詢逆向工程品質報告
      Then reliability 應為 "yellow"（🟡 題庫較少，結構可能不完整）

  # ========== 增量更新 ==========

  Rule: 命令（增量）- 新增考古題後可觸發增量逆向工程

    Example: 追加考古題後更新知識樹
      Given 考科 "信託業業務人員" 已完成考綱逆向工程（180 題）
      And 考科 "信託業業務人員" 新增 50 題考古題
      When 管理員 "admin@example.com" 對考科 "信託業業務人員" 執行增量逆向工程
      Then 操作成功
      And 系統應保留既有節點結構
      And 新題目應被映射到現有或新增的知識節點
      And 出題頻率統計應更新

  # ========== 訂閱限制 ==========

  Rule: 前置（權限）- 知識樹查詢依訂閱方案開放

    Example: FREE 用戶可查看完整知識樹，但 AI 追問限制 3 次/節點
      Given 考科 "信託業業務人員" 已完成考綱逆向工程
      When 使用者 "free@example.com" 查詢考科 "信託業業務人員" 的知識樹
      Then 操作成功
      And 所有節點 locked 應為 false（FREE 可瀏覽全部層級）
      And 每個節點的 AI 教練追問上限為 3 次

    Example: PRO_PLUS 用戶可查看完整知識樹且無追問限制
      Given 考科 "信託業業務人員" 已完成考綱逆向工程
      When 使用者 "pro@example.com" 查詢考科 "信託業業務人員" 的知識樹
      Then 操作成功
      And 所有節點 locked 應為 false
