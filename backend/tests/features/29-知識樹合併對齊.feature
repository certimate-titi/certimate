Feature: 知識樹合併對齊

  同一考科可能有多種來源的知識結構（考古題逆向、教材萃取、手動匯入），
  每次新資料上傳後，系統自動執行合併對齊（Merge & Align），
  確保該考科始終維護唯一一棵統一知識樹（Unified Knowledge Tree）。

  設計原則：
    1. 考綱（考古題逆向）為主幹，教材為補充
    2. 合併以語意相似度比對節點，非字串完全匹配
    3. 每次上傳觸發增量合併，非全量重建
    4. 合併衝突時保留兩個版本，標記待人工審核
    5. 合併完成後下游自動更新（node_mastery、錯題地圖）

  合併管線：
    ┌─────────┐   ┌─────────┐   ┌──────────┐
    │ 考古題    │   │ 教材 PDF │   │ Markdown │
    │ 逆向萃取  │   │ 順向萃取  │   │ 手動匯入  │
    └────┬────┘   └────┬────┘   └────┬─────┘
         │             │             │
         ▼             ▼             ▼
    ┌────────────────────────────────────┐
    │   Merge & Align Pipeline（本 Feature）│
    │                                     │
    │  1. 語意比對：新節點 vs 既有節點       │
    │  2. 匹配 → 合併（補充 metadata）      │
    │  3. 不匹配 → 新增（掛到最近的父節點）  │
    │  4. 衝突 → 標記待審核                 │
    └──────────────┬─────────────────────┘
                   │
                   ▼
         ┌──────────────────┐
         │ Unified Knowledge │
         │      Tree         │
         │  （唯一一棵）       │
         └──────────────────┘
              │         │
         Feature 27  Feature 28
         錯題地圖    難度遞進

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案       | 角色         |
      | 1        | admin@example.com  | ULTRA_1599     | SUPER_ADMIN  |
      | 2        | pro@example.com    | PRO_PLUS_399   | USER         |
    And 系統中有以下考科：
      | 考科 ID | 分類 ID | 名稱         |
      | 1       | 1       | 信託業業務人員 |

  # ========== 上傳觸發合併 ==========

  Rule: 後置（觸發）- 每次新資料上傳後自動觸發知識樹合併對齊

    Example: 第一次上傳考古題 — 建立初始知識樹
      Given 考科 "信託業業務人員" 尚無知識樹
      And 管理員已對考科 "信託業業務人員" 完成考綱逆向工程，產出知識節點：
        | 節點名稱     | 層級 | 父節點    | 來源    |
        | 信託法規     | 1    | null     | exam   |
        | 信託契約     | 2    | 信託法規  | exam   |
        | 受託人義務   | 2    | 信託法規  | exam   |
        | 信託實務     | 1    | null     | exam   |
        | 金錢信託     | 2    | 信託實務  | exam   |
      When 系統執行知識樹合併對齊
      Then 考科 "信託業業務人員" 的統一知識樹應包含 5 個節點
      And 所有節點的 source_origin 應為 "exam"

    Example: 第二次上傳教材 PDF — 增量合併到既有知識樹
      Given 考科 "信託業業務人員" 已有考古題逆向產出的知識樹：
        | 節點名稱     | 層級 | 來源    |
        | 信託法規     | 1    | exam   |
        | 信託契約     | 2    | exam   |
        | 受託人義務   | 2    | exam   |
        | 信託實務     | 1    | exam   |
        | 金錢信託     | 2    | exam   |
      And 使用者 "pro@example.com" 上傳教材 "信託業務教材.pdf"，系統萃取出知識節點：
        | 節點名稱         | 層級 | 父節點    | 來源      |
        | 信託法規概論      | 1    | null     | document |
        | 信託契約要素      | 2    | 信託法規概論 | document |
        | 信託財產獨立性    | 3    | 信託契約要素 | document |
        | 受託人之義務      | 2    | 信託法規概論 | document |
        | 忠實義務         | 3    | 受託人之義務 | document |
        | 信託實務操作      | 1    | null     | document |
        | 金錢信託實務      | 2    | 信託實務操作 | document |
        | 有價證券信託      | 2    | 信託實務操作 | document |
      When 系統執行知識樹合併對齊
      Then 合併結果應為：
        | 既有節點     | 教材節點         | 合併動作                    |
        | 信託法規     | 信託法規概論      | 語意匹配 → 合併（保留既有名稱） |
        | 信託契約     | 信託契約要素      | 語意匹配 → 合併              |
        | —           | 信託財產獨立性    | 新增 → 掛到「信託契約」下      |
        | 受託人義務   | 受託人之義務      | 語意匹配 → 合併              |
        | —           | 忠實義務         | 新增 → 掛到「受託人義務」下    |
        | 信託實務     | 信託實務操作      | 語意匹配 → 合併              |
        | 金錢信託     | 金錢信託實務      | 語意匹配 → 合併              |
        | —           | 有價證券信託      | 新增 → 掛到「信託實務」下      |
      And 統一知識樹應包含 8 個節點（原 5 + 新增 3）
      And 新增的節點 source_origin 應為 "document"
      And 合併的節點應同時保留 exam 和 document 兩個 source_origin

  # ========== 語意比對邏輯 ==========

  Rule: 後置（比對）- 合併使用語意相似度而非字串完全匹配

    Example: 名稱不同但語意相同的節點應合併
      Given 既有知識樹有節點 "受託人義務"
      And 新上傳教材萃取出節點 "受託人之義務"
      When 系統執行語意比對
      Then 兩個節點的語意相似度應大於閾值（>= 0.85）
      And 系統應將兩者合併為同一節點
      And 保留既有名稱 "受託人義務"（主幹優先）

    Example: 語意不同的節點不應合併
      Given 既有知識樹有節點 "金錢信託"
      And 新上傳教材萃取出節點 "不動產信託"
      When 系統執行語意比對
      Then 兩個節點的語意相似度應低於閾值（< 0.85）
      And "不動產信託" 應作為新節點加入知識樹

    Example: 層級也納入比對考量
      Given 既有知識樹有 depth=1 節點 "信託法規" 和 depth=2 節點 "信託契約"
      And 新上傳萃取出 depth=2 節點 "信託法規細則"
      When 系統執行語意比對
      Then "信託法規細則" 不應與 depth=1 的 "信託法規" 合併（層級差異 > 1）
      And "信託法規細則" 應作為 "信託法規" 的子節點新增

  # ========== 合併衝突處理 ==========

  Rule: 後置（衝突）- 語意模糊時標記為待審核

    Example: 相似度介於灰色地帶的節點標記為衝突
      Given 既有知識樹有節點 "信託契約"
      And 新上傳萃取出節點 "信託契約與委任契約之比較"
      When 系統執行語意比對
      Then 語意相似度介於 0.65 至 0.85 之間
      And 系統應標記為合併衝突：
        | 欄位              | 值                          |
        | existing_node    | 信託契約                      |
        | incoming_node    | 信託契約與委任契約之比較         |
        | similarity       | 0.72                         |
        | status           | pending_review                |
        | suggestion       | merge_as_child（建議作為子節點） |

    Example: 管理員可審核並解決合併衝突
      Given 考科 "信託業業務人員" 有 2 筆未解決的合併衝突
      When 管理員 "admin@example.com" 查詢合併衝突清單
      Then 操作成功
      And 回應應包含 2 筆衝突紀錄
      And 每筆應包含：
        | 欄位              | 說明                              |
        | existing_node    | 既有節點名稱                        |
        | incoming_node    | 新進節點名稱                        |
        | similarity       | 語意相似度分數                       |
        | suggestion       | AI 建議動作（merge / merge_as_child / keep_separate） |

    Example: 管理員選擇合併衝突節點
      Given 有一筆合併衝突：既有 "信託契約" vs 新進 "信託契約與委任契約之比較"
      When 管理員 "admin@example.com" 解決衝突，選擇 "merge_as_child"
      Then 操作成功
      And "信託契約與委任契約之比較" 應成為 "信託契約" 的子節點
      And 該衝突狀態應更新為 "resolved"

  # ========== 主幹優先規則 ==========

  Rule: 後置（優先）- 考古題逆向的結構為主幹，教材為補充

    Example: 合併時保留考古題節點的名稱與層級
      Given 既有節點 "信託法規"（source_origin: exam, depth: 1）
      And 新進節點 "信託法規概論"（source_origin: document, depth: 1）
      When 兩者被判定為語意匹配
      Then 合併後節點名稱應為 "信託法規"（保留 exam 來源的名稱）
      And 節點 metadata 應記錄別名 "信託法規概論"

    Example: 教材新增的細節節點掛在考古題主幹下
      Given 既有主幹有 "信託契約"（depth: 2, source_origin: exam）
      And 教材萃取出 "信託財產獨立性"（depth: 3, source_origin: document）
      And AI 判斷 "信託財產獨立性" 語意屬於 "信託契約" 的子概念
      When 系統執行合併
      Then "信託財產獨立性" 應掛在 "信託契約" 下方（depth: 3）
      And 該節點 source_origin 應為 "document"

  # ========== 合併後節點 Metadata ==========

  Rule: 後置（Metadata）- 合併後的節點應保留完整的來源追蹤

    Example: 合併後的節點包含多來源資訊
      Given 節點 "信託契約" 已合併考古題與教材來源
      When 查詢節點 "信託契約" 的詳細資訊
      Then 回應應包含：
        | 欄位                    | 說明                           |
        | name                   | 信託契約                        |
        | aliases                | 教材中的別名陣列（如「信託契約要素」）|
        | source_origins         | ["exam", "document"]           |
        | mapped_question_count  | 來自考古題的題目數               |
        | document_refs          | 來自教材的段落引用               |
        | exam_frequency         | 出題頻率（僅考古題來源有）        |
        | last_merged_at         | 最後一次合併時間                 |

  # ========== 多次上傳的增量合併 ==========

  Rule: 後置（增量）- 每次上傳都是增量合併，非全量重建

    Example: 第三次上傳 YouTube 影片 — 繼續增量合併
      Given 考科 "信託業業務人員" 已有 8 個節點的統一知識樹（考古題 + 教材）
      And 使用者 "pro@example.com" 上傳 YouTube "信託稅制解說"，萃取出：
        | 節點名稱       | 層級 | 來源      |
        | 信託稅制       | 1    | document |
        | 信託課稅原則   | 2    | document |
        | 贈與稅處理     | 2    | document |
      When 系統執行知識樹合併對齊
      Then 統一知識樹應新增 3 個節點（原 8 + 新 3 = 11）
      And 新增節點 source_origin 應為 "document"
      And 既有的 8 個節點不受影響

    Example: 追加考古題後重新對齊題目映射
      Given 考科 "信託業業務人員" 已有統一知識樹
      And 管理員新匯入 50 題考古題到該考科
      When 系統執行知識樹合併對齊
      Then 新題目應被映射到既有節點（語意比對）
      And 各節點的 mapped_question_count 應更新
      And 各節點的 exam_frequency 應重新計算

  # ========== 合併歷史 ==========

  Rule: 查詢（歷史）- 可查看知識樹的合併歷史

    Example: 查詢合併歷史紀錄
      Given 考科 "信託業業務人員" 已執行 3 次合併對齊
      When 管理員 "admin@example.com" 查詢考科 "信託業業務人員" 的合併歷史
      Then 操作成功
      And 回應應包含 3 筆合併紀錄
      And 每筆應包含：
        | 欄位              | 說明                        |
        | merged_at        | 合併時間                     |
        | trigger_source   | 觸發來源（exam / document）   |
        | trigger_name     | 觸發的資源名稱               |
        | nodes_added      | 新增節點數                   |
        | nodes_merged     | 合併節點數                   |
        | conflicts_count  | 衝突數                      |

  # ========== 統一知識樹查詢 ==========

  Rule: 查詢（統一樹）- 使用者查詢的永遠是合併後的統一知識樹

    Example: 使用者查看知識樹時看到的是統一版本
      Given 考科 "信託業業務人員" 已經過多次合併對齊
      When 使用者 "pro@example.com" 查詢考科 "信託業業務人員" 的知識樹
      Then 操作成功
      And 回應為唯一一棵統一知識樹
      And 每個節點可透過 source_origins 辨識其來源
      And 有教材引用的節點可展開查看原文段落

    Example: 統一知識樹匯出為 Markdown 包含來源標記
      Given 考科 "信託業業務人員" 已經過多次合併對齊
      When 使用者 "pro@example.com" 匯出考科 "信託業業務人員" 的知識樹為 Markdown
      Then 內容應包含來源標記，例如：
        """
        # 信託法規 [exam]
        ## 信託契約 [exam, document]
        ### 信託財產獨立性 [document]
        ## 受託人義務 [exam, document]
        ### 忠實義務 [document]
        # 信託實務 [exam]
        ## 金錢信託 [exam, document]
        ## 有價證券信託 [document]
        # 信託稅制 [document]
        ## 信託課稅原則 [document]
        ## 贈與稅處理 [document]
        """

  # ========== 下游聯動 ==========

  Rule: 後置（聯動）- 合併完成後下游 Feature 自動更新

    Example: 合併新增節點後 node_mastery 初始化
      Given 合併後新增了節點 "信託財產獨立性"
      When 使用者 "pro@example.com" 查詢錯題地圖（Feature 27）
      Then 新節點 "信託財產獨立性" 應出現在地圖中
      And 該節點 mastery_rate 應為 null
      And 該節點 color 應為 "gray"（尚未作答）

    Example: 合併後考古題重新映射不影響既有 mastery 數據
      Given 使用者 "pro@example.com" 在節點 "信託契約" 已有 mastery_rate: 65
      And 系統因新上傳觸發合併對齊
      When 合併完成
      Then 節點 "信託契約" 的 mastery_rate 應維持 65（不受合併影響）
