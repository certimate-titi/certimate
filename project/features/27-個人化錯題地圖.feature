@ignore
Feature: 個人化錯題地圖

  將學員的錯題紀錄映射到知識心智圖節點上，
  以紅/橘/綠色視覺化呈現個人弱點分佈，
  驅動 Spec Driven Design 的自適應學習建議。

  核心邏輯：
    - 每次作答結束 → 更新 node_mastery（答對率、顏色）
    - 知識樹 + node_mastery → 個人化錯題熱力圖
    - 熱力圖節點可展開查看該節點下的錯題明細
    - 底層資料為結構化 JSON，前端負責渲染為互動式地圖

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案       | 角色 |
      | 1        | pro@example.com    | PRO_PLUS_399   | USER |
      | 2        | free@example.com   | FREE           | USER |
    And 系統中有以下考科：
      | 考科 ID | 分類 ID | 名稱         |
      | 1       | 1       | 信託業業務人員 |
    And 考科 "信託業業務人員" 已完成考綱逆向工程，知識樹如下：
      | 節點 ID | 名稱             | 層級 | 父節點 ID |
      | 10      | 信託法規          | 1    | null      |
      | 11      | 信託契約          | 2    | 10        |
      | 12      | 信託財產獨立性原則  | 3    | 11        |
      | 13      | 受託人義務        | 2    | 10        |
      | 14      | 忠實義務          | 3    | 13        |
      | 20      | 信託實務          | 1    | null      |
      | 21      | 金錢信託          | 2    | 20        |
      | 22      | 有價證券信託      | 2    | 20        |

  # ========== 答題後更新掌握度 ==========

  Rule: 後置（更新）- 每次考試作答後系統自動更新知識節點掌握度

    Example: 作答結束後自動更新 node_mastery
      Given 使用者 "pro@example.com" 有學習歷程於考科 "信託業業務人員"
      And 使用者 "pro@example.com" 在節點 "信託財產獨立性原則" 的作答紀錄為：
        | 答對數 | 總作答數 |
        | 3      | 10       |
      When 系統更新使用者 "pro@example.com" 的節點掌握度
      Then 節點 "信託財產獨立性原則" 的 mastery_rate 應為 30
      And 節點 "信託財產獨立性原則" 的 color 應為 "red"

    Example: 掌握度顏色規則
      Given 使用者 "pro@example.com" 的各節點掌握度如下：
        | 節點名稱           | 答對率 |
        | 信託財產獨立性原則   | 30%   |
        | 忠實義務           | 65%   |
        | 金錢信託           | 85%   |
        | 有價證券信託        | 0%    |
      Then 各節點顏色應為：
        | 節點名稱           | 預期顏色 | 規則              |
        | 信託財產獨立性原則   | red     | 答對率 < 60%       |
        | 忠實義務           | orange  | 60% <= 答對率 < 80% |
        | 金錢信託           | green   | 答對率 >= 80%       |
        | 有價證券信託        | gray    | 尚未作答            |

  # ========== 錯題地圖查詢 ==========

  Rule: 查詢（地圖）- 使用者可查看個人化錯題熱力地圖

    Example: 查詢個人錯題地圖回傳帶顏色的知識樹
      Given 使用者 "pro@example.com" 有學習歷程於考科 "信託業業務人員"
      And 使用者 "pro@example.com" 已完成多次考試，各節點掌握度已更新
      When 使用者 "pro@example.com" 查詢考科 "信託業業務人員" 的錯題地圖
      Then 操作成功
      And 回應應為帶有 mastery 資訊的知識樹 JSON：
        | 欄位          | 說明                              |
        | nodes        | 知識節點陣列（含 children 巢狀結構）  |
      And 每個節點應包含：
        | 欄位           | 說明                             |
        | id            | 節點 ID                           |
        | name          | 節點名稱                          |
        | depth         | 層級深度                          |
        | mastery_rate  | 答對率（0-100，null 表示未作答）    |
        | color         | red / orange / green / gray       |
        | wrong_count   | 該節點下的累計錯題數               |
        | children      | 子節點陣列                        |

    Example: 父節點掌握度為子節點的加權平均
      Given 使用者 "pro@example.com" 的子節點掌握度如下：
        | 節點名稱           | mastery_rate |
        | 信託財產獨立性原則   | 30           |
        | 忠實義務           | 70           |
      When 使用者 "pro@example.com" 查詢考科 "信託業業務人員" 的錯題地圖
      Then 父節點 "信託法規" 的 mastery_rate 應為子節點的加權平均
      And 父節點 "信託法規" 的 color 應依照計算後的 mastery_rate 決定

  # ========== 節點錯題明細 ==========

  Rule: 查詢（明細）- 點選節點可展開查看該節點的錯題清單

    Example: 查看弱點節點的錯題明細
      Given 使用者 "pro@example.com" 在節點 "信託財產獨立性原則" 有 7 題錯題
      When 使用者 "pro@example.com" 查詢節點 "信託財產獨立性原則" 的錯題明細
      Then 操作成功
      And 回應應包含 7 筆錯題紀錄
      And 每筆錯題應包含：
        | 欄位              | 說明                   |
        | question_id      | 題目 ID                 |
        | content          | 題目內容（前 120 字）    |
        | student_answer   | 學生作答                |
        | correct_answer   | 正確答案                |
        | difficulty       | 難度等級                |
        | exam_date        | 作答日期                |
        | source_type      | historical / ai_generated |

  # ========== 時間軸篩選 ==========

  Rule: 查詢（時間軸）- 錯題地圖支援時間範圍篩選

    Example: 篩選本週的錯題掌握度
      Given 使用者 "pro@example.com" 已在本週和上週分別完成考試
      When 使用者 "pro@example.com" 查詢考科 "信託業業務人員" 的錯題地圖，時間範圍為 "this_week"
      Then 操作成功
      And mastery_rate 僅反映本週的作答結果

    Example: 查看全部歷史的掌握度
      When 使用者 "pro@example.com" 查詢考科 "信託業業務人員" 的錯題地圖，時間範圍為 "all"
      Then 操作成功
      And mastery_rate 反映所有歷史作答的累計結果

  # ========== Markdown 匯出 ==========

  Rule: 後置（匯出）- 錯題地圖可匯出為帶掌握度標記的 Markdown

    Example: 匯出錯題地圖為 Markdown
      Given 使用者 "pro@example.com" 已有完整的錯題地圖資料
      When 使用者 "pro@example.com" 匯出考科 "信託業業務人員" 的錯題地圖為 Markdown
      Then 操作成功
      And 內容應包含掌握度標記，例如：
        """
        # 信託法規 🟡 (55%)
        ## 信託契約 🔴 (30%)
        ### 信託財產獨立性原則 🔴 (30%) — 錯題 7 題
        ## 受託人義務 🟡 (70%)
        ### 忠實義務 🟡 (70%) — 錯題 3 題
        # 信託實務 🟢 (85%)
        ## 金錢信託 🟢 (85%)
        ## 有價證券信託 ⚪ (未作答)
        """

  # ========== 訂閱限制 ==========

  Rule: 前置（權限）- FREE 用戶可查看完整錯題地圖，但 AI 追問限制 3 次/節點

    Example: FREE 用戶可查看完整錯題地圖
      Given 使用者 "free@example.com" 有學習歷程於考科 "信託業業務人員"
      When 使用者 "free@example.com" 查詢考科 "信託業業務人員" 的錯題地圖
      Then 操作成功
      And 所有節點應包含 mastery_rate 與 color（FREE 可瀏覽全部層級）
      And 每個節點的 AI 教練追問上限為 3 次

  # ========== AI 弱點建議 ==========

  Rule: 後置（建議）- 系統應根據錯題地圖生成學習建議

    @ignore
    Example: AI 根據弱點節點生成個人化學習路徑建議
      Given 使用者 "pro@example.com" 的錯題地圖中有 3 個紅色節點
      When 使用者 "pro@example.com" 請求 AI 學習建議
      Then 操作成功
      And 建議應優先針對紅色節點（mastery_rate 最低者）
      And 每條建議應包含：
        | 欄位             | 說明                        |
        | target_node     | 建議加強的知識節點             |
        | current_rate    | 目前掌握度                    |
        | suggested_action | review / quiz / deep_dive   |
        | estimated_time  | 預估學習時間                  |
