@ignore @command
Feature: 可調整考題後端 AI 生成服務 — 多階段 Prompt 流程

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案     |
      | 1        | pro@example.com    | PRO_199      |
      | 2        | ultra@example.com  | ULTRA_1599   |
    And 系統中有以下資源與知識節點：
      | 資源 ID | 使用者 ID | 名稱              | 狀態      |
      | 1       | 1        | AWS_SAA_講義.pdf  | COMPLETED |
    And 系統中有以下知識節點：
      | 節點 ID | 資源 ID | 名稱           | 可出題數 |
      | 1       | 1       | EC2 運算服務   | 20       |
      | 2       | 1       | S3 儲存服務    | 20       |
      | 3       | 1       | IAM 身分管理   | 20       |
    And 系統中有以下 AI Prompt 模板設定：
      | 階段 ID | 階段名稱       | 順序 | 狀態    |
      | 1       | 考點分析       | 1    | active  |
      | 2       | 考題生成       | 2    | active  |
      | 3       | 干擾項優化     | 3    | active  |
      | 4       | 格式化輸出     | 4    | active  |

  # ========== 多階段 Prompt 架構 ==========

  Rule: 後置（流程）- AI 生成服務應依序執行四個階段的 Prompt

    Example: 四階段 Prompt 依序執行並各自產出中間結果
      Given 使用者 "pro@example.com" 已提交合法測驗設定：
        | 欄位         | 值                 |
        | 選擇節點     | 1, 2               |
        | 題數         | 10                 |
        | 難易度分配   | Easy:30% Medium:50% Hard:20% |
      When 後端 AI 生成服務開始處理
      Then 系統應依序執行以下階段：
        | 階段 | 名稱         | 輸入                         | 輸出                            |
        | 1    | 考點分析     | 選定節點的向量化知識內容       | 考綱 JSON（考點列表與出題比例）  |
        | 2    | 考題生成     | 階段 1 考綱 + 難易度分配 + 使用者背景 | 原始考題列表（題幹 + 正確答案）  |
        | 3    | 干擾項優化   | 階段 2 原始考題 + 使用者背景   | 完整考題（含干擾項 + 詳解）      |
        | 4    | 格式化輸出   | 階段 3 完整考題                | 系統標準 JSON Schema             |

  # ========== 個人化：使用者背景注入 Prompt ==========

  Rule: 後置（個人化）- 有填寫個人資料的使用者，其年齡、學歷與職業應作為 Prompt 上下文注入

    Example: 高中學歷使用者生成的考題應避免艱澀術語
      Given 使用者 "pro@example.com" 的個人資料為：
        | 欄位     | 值          |
        | 年齡     | 18          |
        | 最高學歷 | 高中 / 高職 |
        | 職業     | 學生        |
      When 後端 AI 生成服務開始處理
      Then 階段 2 的 Prompt 應包含使用者背景上下文：「使用者為 18 歲高中生，請使用淺顯語言出題」
      And 階段 3 的 Prompt 應包含指示：「解析請使用生活化比喻，避免假設讀者具備進階技術知識」
      And 生成的題目描述應使用白話文而非學術用語

    Example: 碩士學歷工程師使用者生成的考題可直接使用專業術語
      Given 使用者 "ultra@example.com" 的個人資料為：
        | 欄位     | 值           |
        | 年齡     | 30           |
        | 最高學歷 | 碩士         |
        | 職業     | 軟體工程師   |
      When 後端 AI 生成服務開始處理
      Then 階段 2 的 Prompt 應包含使用者背景上下文：「使用者具碩士學歷且為軟體工程師」
      And 生成的題目可直接使用專業術語與技術情境
      And 階段 3 的解析可引用官方文件或 API 語法

    Example: 使用者未填寫個人資料時使用預設中等程度
      Given 使用者 "pro@example.com" 的年齡與學歷欄位皆為空
      When 後端 AI 生成服務開始處理
      Then 系統不應注入個人化上下文至 Prompt
      And 生成的考題應使用預設的大學程度通用語言

  Rule: 後置（進度）- 各階段完成時應透過 SSE 推送進度

    Example: SSE 進度事件對應各階段完成
      Given 使用者 "pro@example.com" 已提交測驗設定並建立測驗任務 ID 為 100
      When 後端 AI 生成服務依序完成各階段
      Then SSE 應依序推送以下進度事件：
        | 進度百分比 | 階段   | 說明訊息                          |
        | 10        | 準備   | 正在從向量庫提取知識點...          |
        | 30        | 階段 1 | AI 正在分析考點與出題比例...       |
        | 50        | 階段 2 | AI 教練正在出題...                |
        | 75        | 階段 3 | AI 教練正在設計考題陷阱與詳解...   |
        | 90        | 階段 4 | 校對格式與排版中...               |
        | 100       | 完成   | 考卷準備完畢！                    |

  # ========== 階段 1：考點分析 ==========

  Rule: 後置（回應）- 階段 1 應從向量庫擷取知識後回傳考綱

    Example: 考點分析階段產出包含比例的考綱
      When 階段 1 Prompt 以節點 1 (EC2) 和節點 2 (S3) 的向量化內容為輸入
      Then 階段 1 輸出應包含：
        | 欄位            | 說明                     |
        | exam_points     | 5-10 個核心考點列表       |
        | point_ratio     | 各考點建議出題比例 (%)    |
        | difficulty_map  | 各考點建議難度分布        |
      And 所有 point_ratio 加總應等於 100%

  # ========== 階段 2：考題生成 ==========

  Rule: 後置（回應）- 階段 2 應根據考綱生成原始考題

    Example: 考題生成階段產出含題幹與正確答案的原始考題
      Given 階段 1 已輸出含 5 個考點、各 2 題的考綱
      When 階段 2 Prompt 以階段 1 輸出與難易度分配為輸入
      Then 階段 2 輸出應包含 10 題原始考題
      And 每題應包含：
        | 欄位          | 說明                  |
        | question_text | 題幹                  |
        | correct_answer| 正確答案文字          |
        | difficulty    | easy / medium / hard  |
        | exam_point    | 對應考點名稱          |
      And 難易度分布應符合 Easy:30% Medium:50% Hard:20%（容許 ±1 題）

  # ========== 階段 3：干擾項優化 ==========

  Rule: 後置（回應）- 階段 3 應為每題設計三個高誘答性干擾項並撰寫詳解

    Example: 干擾項優化階段補齊選項與解析
      Given 階段 2 已輸出 10 題原始考題
      When 階段 3 Prompt 以階段 2 輸出為輸入
      Then 階段 3 輸出中每題應包含：
        | 欄位               | 說明                              |
        | options            | 4 個選項（含 1 個正確 + 3 個干擾） |
        | correct_index      | 正確答案的索引 (0-3)               |
        | explanation        | 正確答案的詳細解析                 |
        | distractor_reasons | 各干擾項錯誤原因說明               |
      And 干擾項應具備「表面合理但本質錯誤」的特性
      And 正確答案在四個選項中的位置應隨機分布

  # ========== 階段 4：格式化輸出 ==========

  Rule: 後置（回應）- 階段 4 應輸出符合系統 JSON Schema 的結構化資料

    Example: 格式化輸出符合標準 Schema
      Given 階段 3 已輸出 10 題完整考題
      When 階段 4 Prompt 以階段 3 輸出為輸入
      Then 階段 4 輸出應為合法 JSON 且符合以下 Schema：
        """json
        {
          "exam_id": "string",
          "total_questions": 10,
          "questions": [
            {
              "id": "string",
              "text": "題幹文字",
              "options": ["選項A", "選項B", "選項C", "選項D"],
              "answer": 0,
              "difficulty": "medium",
              "exam_point": "考點名稱",
              "explanation": "詳細解析文字",
              "distractor_reasons": {
                "1": "干擾項B錯誤原因",
                "2": "干擾項C錯誤原因",
                "3": "干擾項D錯誤原因"
              }
            }
          ]
        }
        """

  # ========== Prompt 模板管理 ==========

  Rule: 前置（權限）- 僅 admin 與 super_admin 可修改 Prompt 模板

    Example: 一般用戶嘗試修改 Prompt 模板失敗
      When 使用者 "pro@example.com" 嘗試修改階段 1 的 Prompt 模板
      Then 操作失敗，錯誤為「權限不足」

  Rule: 後置（狀態）- 修改 Prompt 模板後應生效於後續考題生成

    Example: 管理員更新階段 3 的 Prompt 模板
      Given 管理員登入系統
      When 管理員修改階段 3 Prompt 模板，新增指示「干擾項應包含常見的中文翻譯錯誤」
      Then 操作成功
      And 階段 3 Prompt 模板的版本號應遞增
      And 後續生成的考題應使用新版 Prompt 模板

    Example: 查看 Prompt 模板的歷史版本
      Given 管理員登入系統
      When 管理員查看階段 3 Prompt 模板的歷史版本
      Then 回應應包含所有歷史版本：
        | 版本 | 修改時間            | 修改者             |
        | v1   | 2026-03-01 00:00:00 | admin@certimate.com |
        | v2   | 2026-03-26 10:00:00 | admin@certimate.com |

  # ========== 錯誤處理 ==========

  Rule: 後置（異常）- AI 生成中間階段失敗時應可重試

    Example: 階段 2 AI 呼叫逾時後自動重試
      Given 階段 1 已成功完成
      When 階段 2 AI API 呼叫出現逾時錯誤
      Then 系統應自動重試最多 3 次，每次間隔 2 秒
      And SSE 應推送重試訊息 "AI 回應較慢，正在重試 (1/3)..."

    Example: 重試三次仍失敗時標記任務為失敗
      Given 階段 2 AI API 呼叫已重試 3 次仍失敗
      Then 測驗任務狀態應更新為 "FAILED"
      And SSE 應推送錯誤事件：
        | 欄位     | 值                                    |
        | status   | error                                 |
        | message  | AI 生成失敗，請稍後重新嘗試            |
        | stage    | 2                                     |
      And 系統應記錄詳細錯誤日誌

  Rule: 後置（異常）- AI 輸出格式驗證失敗時應重新生成該階段

    Example: 階段 4 輸出不符合 JSON Schema 時自動重新生成
      Given 階段 4 AI 輸出的 JSON 缺少 "explanation" 欄位
      When 系統驗證發現格式不符
      Then 系統應自動為階段 4 補充指示並重新生成
      And 重新生成的補充指令應包含具體缺失欄位的提示
