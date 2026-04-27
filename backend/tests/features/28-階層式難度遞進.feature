@backend
Feature: 階層式難度遞進

  當學員在某知識節點答錯時，系統沿知識樹向上回溯至父節點，
  降階出更基礎的題目，直到學員重新掌握後再遞進回原層級。

  核心演算法：
    1. 學員答錯節點 X（depth=3）的題目
    2. 系統回溯到父節點 P（depth=2），出基礎題
    3. 若父節點也答錯 → 繼續回溯到祖父節點（depth=1）
    4. 學員在低層級答對 → 逐步遞進回高層級
    5. 最終目標：確保知識地基穩固後再挑戰進階題

  與錯題地圖的關聯：
    - 回溯時，錯題地圖上對應節點閃爍提示「正在補強基礎」
    - 遞進成功後，節點顏色即時從紅/橘轉為橘/綠

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案       | 角色 |
      | 1        | pro@example.com    | PRO_PLUS_399   | USER |
      | 2        | free@example.com   | FREE           | USER |
    And 系統中有以下考科：
      | 考科 ID | 分類 ID | 名稱         |
      | 1       | 1       | 信託業業務人員 |
    And 考科 "信託業業務人員" 的知識樹如下：
      | 節點 ID | 名稱             | 層級 | 父節點 ID | 難度基準    |
      | 10      | 信託法規          | 1    | null      | easy       |
      | 11      | 信託契約          | 2    | 10        | medium     |
      | 12      | 信託財產獨立性原則  | 3    | 11        | hard       |
      | 13      | 受託人義務        | 2    | 10        | medium     |
      | 14      | 忠實義務          | 3    | 13        | hard       |
      | 20      | 信託實務          | 1    | null      | easy       |
      | 21      | 金錢信託          | 2    | 20        | medium     |

  # ========== 答錯觸發回溯 ==========

  Rule: 後置（回溯）- 學員在進階節點答錯時系統自動回溯到父節點

    Example: 在 depth=3 的節點答錯後回溯到 depth=2
      Given 使用者 "pro@example.com" 正在練習節點 "信託財產獨立性原則"（depth=3）
      And 使用者連續答錯 2 題
      When 系統計算下一題的出題策略
      Then 系統應回溯到父節點 "信託契約"（depth=2）
      And 下一題的難度應為 "medium"（父節點的難度基準）
      And 回應應包含：
        | 欄位              | 值                  |
        | backtrack_from   | 信託財產獨立性原則     |
        | backtrack_to     | 信託契約             |
        | reason           | 連續答錯，需鞏固基礎   |

    Example: 在 depth=2 的節點也答錯時繼續回溯到 depth=1
      Given 使用者 "pro@example.com" 已從 "信託財產獨立性原則" 回溯到 "信託契約"
      And 使用者在 "信託契約" 又連續答錯 2 題
      When 系統計算下一題的出題策略
      Then 系統應回溯到根節點 "信託法規"（depth=1）
      And 下一題的難度應為 "easy"

    Example: 已在根節點時不再回溯
      Given 使用者 "pro@example.com" 已在根節點 "信託法規"（depth=1）
      And 使用者在 "信託法規" 連續答錯 2 題
      When 系統計算下一題的出題策略
      Then 系統應維持在根節點 "信託法規" 出題
      And 下一題的難度應維持 "easy"
      And 回應應包含 hint: "建議複習此章節的基礎教材"

  # ========== 回溯觸發條件 ==========

  Rule: 前置（條件）- 回溯觸發條件可由系統設定

    Example: 預設連續答錯 2 題觸發回溯
      Given 系統的回溯觸發條件為「連續答錯 2 題」
      And 使用者 "pro@example.com" 在節點 "忠實義務" 答對 1 題後答錯 1 題
      When 系統計算下一題的出題策略
      Then 系統不應觸發回溯（未達連續 2 題門檻）
      And 下一題仍在節點 "忠實義務" 出題

    Example: 節點答對率低於門檻也觸發回溯
      Given 系統的回溯觸發條件包含「節點答對率 < 40%」
      And 使用者 "pro@example.com" 在節點 "忠實義務" 的答對率為 35%（答對 7 / 總 20）
      When 系統計算下一題的出題策略
      Then 系統應觸發回溯到父節點 "受託人義務"

  # ========== 答對後遞進 ==========

  Rule: 後置（遞進）- 學員在低層級答對後系統自動遞進回高層級

    Example: 在父節點連續答對後遞進回原節點
      Given 使用者 "pro@example.com" 從 "信託財產獨立性原則" 回溯到 "信託契約"
      And 使用者在 "信託契約" 連續答對 3 題
      When 系統計算下一題的出題策略
      Then 系統應遞進回 "信託財產獨立性原則"（depth=3）
      And 回應應包含：
        | 欄位              | 值                        |
        | progress_from    | 信託契約                    |
        | progress_to      | 信託財產獨立性原則            |
        | reason           | 基礎已鞏固，挑戰進階題       |

    Example: 遞進後答錯可再次回溯
      Given 使用者 "pro@example.com" 剛從 "信託契約" 遞進回 "信託財產獨立性原則"
      And 使用者在 "信託財產獨立性原則" 又連續答錯 2 題
      When 系統計算下一題的出題策略
      Then 系統應再次回溯到 "信託契約"

  # ========== 遞進觸發條件 ==========

  Rule: 前置（條件）- 遞進條件可由系統設定

    Example: 預設連續答對 3 題觸發遞進
      Given 系統的遞進觸發條件為「連續答對 3 題」
      And 使用者 "pro@example.com" 在父節點 "信託契約" 答對 2 題
      When 系統計算下一題的出題策略
      Then 系統不應觸發遞進（未達連續 3 題門檻）
      And 下一題仍在 "信託契約" 出題

  # ========== 出題策略 API ==========

  Rule: 查詢（策略）- API 回傳完整的出題策略決策

    Example: 查詢當前出題策略
      Given 使用者 "pro@example.com" 正在進行自適應練習
      When 使用者 "pro@example.com" 請求下一題
      Then 操作成功
      And 回應應包含出題策略：
        | 欄位               | 說明                                   |
        | current_node      | 當前出題節點名稱                         |
        | current_depth     | 當前出題層級                             |
        | original_node     | 原始目標節點（若已回溯則與 current 不同）  |
        | difficulty        | 出題難度                                 |
        | backtrack_count   | 已回溯次數                               |
        | next_action       | stay / backtrack / progress              |
      And 回應應包含題目：
        | 欄位             | 說明               |
        | question_id     | 題目 ID             |
        | content         | 題目內容             |
        | options         | 選項（A/B/C/D）     |
        | source_type     | historical / ai_generated |
        | node_name       | 對應知識節點          |

  # ========== 學習軌跡紀錄 ==========

  Rule: 後置（紀錄）- 系統應記錄完整的回溯/遞進軌跡

    Example: 記錄一次完整的回溯→遞進學習軌跡
      Given 使用者 "pro@example.com" 完成一輪自適應練習，軌跡如下：
        | 步驟 | 節點             | 動作       | 結果     |
        | 1   | 信託財產獨立性原則 | 作答       | 答錯 ×2  |
        | 2   | 信託契約          | 回溯作答   | 答對 ×3  |
        | 3   | 信託財產獨立性原則 | 遞進作答   | 答對 ×2  |
      When 使用者 "pro@example.com" 查詢本次練習的學習軌跡
      Then 操作成功
      And 回應應包含 3 筆軌跡紀錄
      And 軌跡應清楚標記每一步的 backtrack / progress 動作

  # ========== 與錯題地圖聯動 ==========

  Rule: 後置（聯動）- 回溯/遞進結果即時反映到錯題地圖

    Example: 遞進成功後節點顏色應更新
      Given 使用者 "pro@example.com" 節點 "信託契約" 原本為 red（答對率 35%）
      And 使用者在回溯練習中於 "信託契約" 額外答對 5 題
      When 使用者 "pro@example.com" 查詢錯題地圖
      Then 節點 "信託契約" 的 mastery_rate 應已更新（反映新的答對紀錄）
      And 節點顏色應依新的 mastery_rate 重新計算

  # ========== 訂閱限制 ==========

  Rule: 前置（權限）- 自適應練習依訂閱方案開放

    Example: FREE 用戶無法使用自適應難度遞進
      When 使用者 "free@example.com" 請求自適應練習
      Then 操作失敗，錯誤為「自適應難度遞進功能為 PRO_PLUS 以上方案專屬」

    Example: PRO_PLUS 用戶可使用自適應練習
      When 使用者 "pro@example.com" 請求自適應練習
      Then 操作成功
