Feature: 信心度校準

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案   |
      | 1        | pro@example.com    | PRO_199    |
      | 2        | free@example.com   | FREE       |
    And 系統中有以下測驗：
      | 測驗 ID | 使用者 ID | 狀態        | 總題數 | 考試時長（分鐘） |
      | 1       | 1        | READY       | 10     | 30              |
      | 2       | 1        | SUBMITTED   | 10     | 30              |
    And 測驗 1 包含以下題目：
      | 題目 ID | 題號 | 題目內容                          | 正確答案 |
      | 101     | 1    | AWS S3 的儲存類型何者最便宜？      | C       |
      | 102     | 2    | EC2 定價模式中何者最具彈性？       | A       |
      | 103     | 3    | IAM Policy 的評估順序為何？        | B       |
    And 測驗 2 的作答記錄含信心度：
      | 題目 ID | 選擇答案 | 正確答案 | 作答正確 | 信心度     |
      | 201     | A        | A       | 是       | confident  |
      | 202     | B        | C       | 否       | confident  |
      | 203     | C        | C       | 是       | guessing   |
      | 204     | A        | B       | 否       | guessing   |
      | 205     | D        | D       | 是       | somewhat   |

  # ========== 作答時的信心度標記 ==========

  Rule: 後置（狀態）- 使用者選擇答案後可標記對該題的信心程度

    Example: 選擇答案後標記信心度為「非常確定」
      Given 使用者 "pro@example.com" 已開始測驗 1
      When 使用者 "pro@example.com" 在題目 101 選擇答案 "C" 並標記信心度為 "confident"
      Then 題目 101 的暫存作答應為 "C"
      And 題目 101 的信心度應為 "confident"

    Example: 選擇答案後標記信心度為「完全猜測」
      Given 使用者 "pro@example.com" 已開始測驗 1
      When 使用者 "pro@example.com" 在題目 102 選擇答案 "A" 並標記信心度為 "guessing"
      Then 題目 102 的信心度應為 "guessing"

    Example: 未標記信心度時預設為「有點把握」
      Given 使用者 "pro@example.com" 已開始測驗 1
      When 使用者 "pro@example.com" 在題目 103 選擇答案 "B" 且未標記信心度
      Then 題目 103 的信心度應預設為 "somewhat"

  # ========== 信心度等級定義 ==========

  Rule: 前置（參數）- 信心度分為三個等級

    Example: 系統支援的信心度等級
      Then 信心度等級應包含：
        | 等級       | 顯示文字 | 圖示 |
        | guessing   | 完全猜測 | 😰   |
        | somewhat   | 有點把握 | 😐   |
        | confident  | 非常確定 | 😎   |

  # ========== 四象限分析 ==========

  Rule: 後置（回應）- 測驗結果頁應提供信心度四象限分析

    Example: 測驗結果顯示信心度四象限統計
      When 使用者 "pro@example.com" 查看測驗 2 的信心度分析
      Then 結果應包含四象限統計：
        | 象限                | 信心度     | 作答結果 | 題數 | 說明         |
        | confident_correct   | confident  | 正確     | 1    | 真正掌握     |
        | confident_incorrect | confident  | 錯誤     | 1    | 危險盲點     |
        | guessing_correct    | guessing   | 正確     | 1    | 幸運猜對     |
        | guessing_incorrect  | guessing   | 錯誤     | 1    | 預期中的弱點 |

    Example: 「危險盲點」題目應以紅色警示標記並優先排入複習
      When 使用者 "pro@example.com" 查看測驗 2 的信心度分析
      Then "confident_incorrect" 象限應標示為紅色警示
      And 該象限的題目應標記為「高優先複習」
      And AI 教練應針對「危險盲點」題目提供額外說明：「您對這題很有把握但答錯了，這是最需要釐清的認知盲點」

    Example: 「幸運猜對」題目應建議加強學習
      When 使用者 "pro@example.com" 查看測驗 2 的信心度分析
      Then "guessing_correct" 象限應標示為黃色提醒
      And AI 教練應建議：「這些題目雖然答對，但您不太確定，建議加強相關知識點」

  # ========== 信心度與間隔複習整合 ==========

  Rule: 後置（排程）- 信心度影響間隔複習排程的優先級

    Example: 「危險盲點」題目的複習間隔應縮短
      Given 使用者 "pro@example.com" 完成測驗，題目 202 為 confident + 錯誤（危險盲點）
      When 系統計算下次複習排程
      Then 題目 202 的下次複習間隔應為 12 小時（比標準 24 小時更短）
      And 題目 202 的 ease_factor 應額外降低 0.3（因為存在認知偏誤）

    Example: 「幸運猜對」題目應排入複習（雖然答對）
      Given 使用者 "pro@example.com" 完成測驗，題目 203 為 guessing + 正確（幸運猜對）
      When 系統計算下次複習排程
      Then 題目 203 應排入複習排程（不因答對而跳過）
      And 題目 203 的下次複習間隔應為 48 小時

    Example: 「真正掌握」題目維持標準間隔複習
      Given 使用者 "pro@example.com" 完成測驗，題目 201 為 confident + 正確（真正掌握）
      When 系統計算下次複習排程
      Then 題目 201 的下次複習間隔應為標準間隔（依 SM-2 演算法）

  # ========== 信心度趨勢追蹤 ==========

  Rule: 後置（回應）- 儀表板應顯示信心度校準趨勢

    Example: 個人儀表板顯示近期測驗的信心校準率
      Given 使用者 "pro@example.com" 已完成 5 場含信心度的測驗
      When 使用者查看個人儀表板的信心校準區塊
      Then 應顯示「信心校準率」指標（confident 且答對的比例）
      And 應顯示近 5 場測驗的校準率趨勢折線圖
      And 校準率超過 80% 時應標示為「校準良好」

  # ========== UI 元件 ==========

  Rule: 後置（回應）- 信心度標記 UI 應簡潔不干擾作答節奏

    Example: 信心度標記以三個小圖示呈現在答案選項下方
      Given 使用者 "pro@example.com" 已開始測驗 1
      When 使用者 "pro@example.com" 在題目 101 選擇答案 "C"
      Then 答案選項下方應出現信心度標記列：😰 😐 😎
      And 預設選中 😐（有點把握）
      And 點擊圖示即可切換信心度，無需額外確認

  Rule: 後置（回應）- 題號導覽網格應以不同底色標示信心度

    Example: 題號導覽網格顯示信心度顏色
      Given 使用者 "pro@example.com" 已開始測驗 1
      And 使用者已作答題目 101（confident）和題目 102（guessing）
      When 使用者查看題號導覽網格
      Then 題目 101 的題號應帶有綠色底框（confident）
      And 題目 102 的題號應帶有橘色底框（guessing）
      And 題目 103 的題號應為灰色（未作答）

  # ─────────────────────────────────────────────
  # EPIC-035 M3：盲推論作答（反錨定 anti-anchoring）
  # ─────────────────────────────────────────────

  @epic-035
  Rule: 後置（反錨定）- needs_answer 題作答時先不揭曉 AI 推論，提交後才揭曉

    Example: 使用者盲作答後 API 揭曉 AI 推論與推理
      Given 使用者 "pro@example.com" 有一個 needs_answer 個人題庫題目，AI 推論答案為 "B"、信心度 0.65
      When 使用者 "pro@example.com" 對該題提交盲作答答案 "A"
      Then 操作成功
      And 回應欄位 "user_answer" 應為 "A"
      And 回應欄位 "ai_inferred_answer" 應為 "B"
      And 回應欄位 "next_step" 應為 "submit_judgment"

  @epic-035
  Rule: 後置（判定）- 盲推論揭曉後可記錄「同意自己/同意AI/都不對」三段狀態

    Example: 使用者提交「同意自己」判定後記錄於題目
      Given 使用者 "pro@example.com" 有一個 needs_answer 個人題庫題目，AI 推論答案為 "B"、信心度 0.65
      When 使用者 "pro@example.com" 對該題提交推論判定 "agree_self"
      Then 操作成功
      And 回應欄位 "judgment" 應為 "agree_self"
      And DB 中該題 explanation 欄位應包含 "user_judgment:agree_self"

  @epic-035
  Rule: 前置（守門）- 非 needs_answer 題走盲推論 API 應拒絕

    Example: 一般 T1 題（answer_source=from_source）提交盲作答回 400
      Given 使用者 "pro@example.com" 有一個 T1 個人題庫題目，正解為 "C"、answer_source=from_source
      When 使用者 "pro@example.com" 對該題提交盲作答答案 "A"
      Then 操作失敗狀態碼為 400
      And 錯誤訊息應包含「此題不屬於 needs_answer」
