Feature: 考古題現代化匯入 (Modern PDF Extraction Pipeline)
  # 使用 Claude Vision + Structured Outputs 取代傳統正則表達式爬蟲
  # 支援組合式題 (combination questions) 與完整驗證閘

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 | 角色  |
      | admin     | admin@example.com  | ULTRA    | 平台管理員 |
      | user1     | user1@example.com  | PRO_199    | 一般使用者 |
    And 系統已準備以下測試用 PDF：
      | PDF 名稱 | 類型 | 題數 | 特性 |
      | normal_questions.pdf | 試題 | 50 | 正常格式(4選項) |
      | normal_answers.pdf | 答案 | 50 | 對應答案鍵 |
      | combination_questions.pdf | 試題 | 30 | 組合式題(部分選項) |
      | combination_answers.pdf | 答案 | 30 | 對應答案鍵 |
      | mismatch_questions.pdf | 試題 | 25 | 題數25 |
      | mismatch_answers.pdf | 答案 | 20 | 答案題數20 |
      | broken_answers.pdf | 答案 | 50 | 答案指向空選項 |

  Rule: 提取與驗證 (Extraction & Validation)

    Example: 正常題目與答案提取成功
      When 平台管理員上傳考古題 PDF，試題為 normal_questions.pdf，答案為 normal_answers.pdf
      And 提交參數：
        | exam_code | P |
        | category_code | 01 |
        | subject_code | 0101 |
        | exam_name | 114年初等考試 |
      Then 提取操作應成功
      And 應返回驗證報告，包含：
        | 字段 | 預期值 |
        | extraction_successful | true |
        | total_questions | 50 |
        | valid_questions | 50 |
        | invalid_questions | 0 |
        | can_import | true |
      And 應解析出 50 個標準化問題結構，每個包含：
        | 字段 | 驗證 |
        | question_number | 整數 1-50 |
        | question_text | 長度 > 10 字 |
        | options.A | 非空字串 |
        | options.B | 非空字串 |
        | options.C | 非空字串 |
        | options.D | 非空字串 |
        | has_image | 布林值 |

    Example: 組合式題 (部分選項) 正確處理
      When 平台管理員上傳考古題 PDF，試題為 combination_questions.pdf，答案為 combination_answers.pdf
      And 提交參數：
        | exam_code | P |
        | category_code | 01 |
        | subject_code | 0102 |
      Then 提取操作應成功
      And 應返回驗證報告，包含：
        | 字段 | 預期值 |
        | extraction_successful | true |
        | total_questions | 30 |
        | valid_questions | 30 |
        | can_import | true |
      And 應正確處理組合式題，例如 Q5：
        | 字段 | 值 |
        | options.A | "政府應保護人民知識產權" |
        | options.B | null |
        | options.C | "著作權可無限期續展" |
        | options.D | null |
        | available_options | ["A", "C"] |
      And 答案 "A" 應指向非空選項（驗證通過）

    Example: 題數不匹配，驗證失敗
      When 平台管理員上傳考古題 PDF，試題為 mismatch_questions.pdf，答案為 mismatch_answers.pdf
      Then 提取操作應成功（暫時）
      And 應返回驗證報告，包含：
        | 字段 | 預期值 |
        | extraction_successful | true |
        | validation.critical_errors[0] | 包含 "Question count mismatch" |
        | can_import | false |
      And 詳細錯誤應說明：預期 25 題，實際 20 題

    Example: 答案指向空選項（關鍵驗證）
      When 平台管理員上傳考古題 PDF，試題為 combination_questions.pdf，答案為 broken_answers.pdf
      Then 提取操作應成功（暫時）
      And 應返回驗證報告，包含 CRITICAL 錯誤：
        | 問題 | 錯誤訊息 |
        | Q3 | "CRITICAL: Correct answer 'B' is empty/missing in PDF. Available options: ['A', 'C', 'D']" |
      And 可導入旗標應為 false
      And 詳細驗證應包含無法匯入的原因清單

  Rule: 驗證閘 (Validation Gates)

    Example: Gate 1 - 題數檢查
      When 試題 PDF 含 50 題，答案 PDF 含 48 個答案
      Then 驗證應失敗，critical_errors 應包含：
        | 錯誤 | "Question count mismatch: 50 questions but 48 expected" |
        | 嚴重性 | CRITICAL |

    Example: Gate 2 - 順序編號檢查
      When 問題編號為 [1, 2, 4, 5, 6]（缺少 3）
      Then 驗證應失敗，critical_errors 應包含：
        | 錯誤 | 包含 "Non-sequential" |
        | 嚴重性 | CRITICAL |

    Example: Gate 3 - 文本長度異常檢查
      When Q15 問題文本超過 2000 字
      Then 驗證應警告，warnings 應包含：
        | 警告 | 包含 "suspiciously long" |
        | 嚴重性 | WARNING |
      And 可導入旗標應為 true（非關鍵）

    Example: Gate 4 - 答案有效性檢查（最關鍵）
      When Q5 選項為 { A: "文字", B: null, C: "文字", D: null }，correct_answer 為 "B"
      Then 驗證應失敗，critical_errors 應包含：
        | 錯誤 | "CRITICAL: Correct answer 'B' is empty/missing in PDF" |
        | 嚴重性 | CRITICAL |
      And 根本原因 | 防止 1,221 題資料損毀問題 |

    Example: Gate 5 - 選項不足檢查
      When Q8 僅有 1 個選項 { A: "文字", B: null, C: null, D: null }
      Then 驗證應失敗，critical_errors 應包含：
        | 錯誤 | "Insufficient options" |

    Example: Gate 6 - 答案覆蓋檢查
      When Q25 不存在於答案 PDF 中
      Then 驗證應失敗，critical_errors 應包含：
        | 錯誤 | 包含 "No answer found for question 25" |

  Rule: 匯入操作 (Import Operations)

    Example: 完整匯入流程（驗證通過）
      When 平台管理員呼叫 /api/v1/exam-import/import 端點
      And 上傳：trial_questions.pdf（50題）、trial_answers.pdf（50答案）
      And 參數為 exam_code="P", category_code="01", subject_code="0101"
      Then 匯入應成功，回應應包含：
        | 字段 | 值 |
        | import_success | true |
        | message | "Successfully imported 50 questions" |
        | exam_info.total_questions | 50 |
        | exam_info.questions_with_answer | 50 |
        | can_import | true |
      And 應包含準備好的匯入資料結構（legacy 格式）

    Example: 匯入失敗（驗證無法通過）
      When 平台管理員呼叫 /api/v1/exam-import/import 端點
      And 上傳：broken_questions.pdf，broken_answers.pdf
      And skip_validation 為 false（預設）
      Then 匯入應失敗，回應應包含：
        | 字段 | 值 |
        | import_success | false |
        | message | 包含 "Validation failed" |
        | validation.can_proceed | false |
        | validation.critical_errors | 非空陣列 |

    Example: 跳過驗證匯入（管理員權限）
      When 平台管理員呼叫 /api/v1/exam-import/import 端點
      And 上傳：broken_questions.pdf，broken_answers.pdf
      And skip_validation 為 true
      Then 匯入應成功（略過驗證）
      And 應記錄警告：檔案因管理員命令略過驗證

  Rule: 僅提取與驗證 (Extract Only)

    Example: 預檢驗證（不匯入）
      When 平台管理員呼叫 /api/v1/exam-import/extract 端點
      And 上傳：test_questions.pdf（50題）、test_answers.pdf（50答案）
      Then 操作應成功，回應應包含：
        | 字段 | 含義 |
        | extraction_successful | true |
        | exam_info | 試卷基本資訊 |
        | validation | 完整驗證報告 |
        | can_import | 是否可匯入 |
      And 應 NOT 將任何資料寫入資料庫

  Rule: 錯誤與邊界情況 (Error Cases)

    Example: PDF 檔案無效
      When 平台管理員上傳無效 PDF（損毀或空檔案）
      Then 操作應失敗，錯誤訊息：
        | 錯誤 | "Question PDF is empty or invalid" |

    Example: PDF 無法被 Claude Vision 解析
      When PDF 格式為不支援的類型（純圖像、密碼保護等）
      Then 操作應失敗，錯誤訊息：
        | 錯誤 | 包含 "Failed to extract questions from PDF" |
        | 詳情 | list of extraction errors |

    Example: JSON 解析失敗
      When Claude 回應無法轉換為 JSON
      Then 操作應失敗，詳情應包含：
        | 錯誤 | "Failed to parse JSON from Claude response" |

    Example: 驗證報告完整性
      When 驗證失敗時
      Then 回應應包含：
        | 欄位 | 說明 |
        | validation_details | 每個問題的詳細驗證結果 |
        | critical_errors | 列表所有關鍵錯誤 |
        | warnings | 列表所有警告 |
        | can_proceed | 最終決定旗標 |

  Rule: 資料轉換與相容性 (Data Conversion)

    Example: 轉換為 Legacy 格式
      Given 提取成功，得到 ExamPaperData（modern format）
      When 系統呼叫 convert_to_legacy_format()
      Then 應輸出 LegacyImportOutput，包含：
        | 字段 | 內容 |
        | import_meta | source, exam_code, total_questions 等 |
        | questions[0].question_number | 題號 |
        | questions[0].content | 題目文字 |
        | questions[0].option_a | 選項A（空字串如果為 null） |
        | questions[0].option_b | 選項B（空字串如果為 null） |
        | questions[0].option_c | 選項C（空字串如果為 null） |
        | questions[0].option_d | 選項D（空字串如果為 null） |
        | questions[0].correct_answer | 正確答案 |
        | questions[0].explanation | 解析（預設空） |
        | questions[0].bloom_category | Bloom 層級（null） |

    Example: 組合式題轉換至 Legacy 格式
      Given 組合式題 Q5: { A: "文字", B: null, C: "文字", D: null }
      When 轉換至 legacy 格式
      Then 應轉換為：
        | 字段 | 值 |
        | option_a | "文字" |
        | option_b | "" |
        | option_c | "文字" |
        | option_d | "" |
      And 應保留原始選項順序

  Rule: 驗證架構端點 (Schema Endpoint)

    Example: 取得驗證閘說明
      When 使用者呼叫 GET /api/v1/exam-import/validation-schema
      Then 應返回驗證規則文件，包含：
        | 項目 | 內容 |
        | validation_gates | 6 個驗證閘的詳細說明 |
        | combination_style_questions | 組合式題解釋與範例 |
        | 每個閘的欄位 | name, description, severity, rule, rationale |

Feature: 考古題資料庫集成 (Phase 2: Database Integration)

  Background:
    Given 資料庫已清空歷史考試與題目

  Rule: 基本匯入與持久化 (Basic Import & Persistence)

    Example: 成功匯入後題目應被寫入資料庫
      When 使用 HistoricalExamImportService 匯入 50 題考古題
      Then 資料庫應包含 1 個新的 HistoricalExam 記錄
      And 資料庫應包含 50 個新的 Question 記錄
      And 所有題目應具有 historical_exam_id 外鍵
      And 題目內容應完整保留（content, options, answer）
      And 匯入結果應包含 exam_id 且 questions_imported > 0

    Example: 題目應可透過 API 查詢
      When 使用 HistoricalExamImportService 匯入 25 題考古題
      Then 可透過 GET /api/v1/exam-import/exams/... 查詢匯入的考古題
      And 可透過 GET /api/v1/exam-import/exams/.../questions 檢索題目
      And 驗證 POST /api/v1/exam-import/exams/.../validate 應通過

  Rule: 重複匯入防護 (Duplicate Import Protection)

    Example: 重複匯入同一份考古題應被拒絕
      Given 系統中已匯入考古題：TEST/00/0000
      When 重新匯入同一份考古題（skip_existing=false）
      Then 重複匯入應返回 success=false 且 message 包含 'already exists'
      And 資料庫應仍包含 1 個 HistoricalExam 記錄

    Example: 使用 skip_existing=true 應安全略過重複
      Given 系統中已匯入考古題：TEST/00/0000
      When 重新匯入同一份考古題（skip_existing=true）
      Then 跳過重複匯入（skip=true）應返回 success=false 但標記為已跳過
      And 資料庫應仍包含 1 個 HistoricalExam 記錄

  Rule: 資料完整性與驗證 (Data Integrity & Validation)

    Example: 匯入時間戳應被記錄
      When 使用 HistoricalExamImportService 匯入 10 題考古題
      Then 匯入日期應被記錄在 HistoricalExam.created_at
      And 驗證模型應為 'modern_pdf_pipeline_v1'

    Example: 批量插入應是 ACID 合規（全有或全無）
      When 使用 HistoricalExamImportService 匯入 50 題考古題
      Then 交易應是 ACID 合規（成功或完全回滾）
      And 批量插入效能應 < 500ms（50 題）

  Rule: 匯入統計管理 (Import Statistics)

    Example: 可列出所有已匯入的考古題
      When 使用 HistoricalExamImportService 匯入 30 題考古題
      Then 呼叫 GET /api/v1/exam-import/exams 應返回匯入記錄列表

    Example: 查詢特定考古題的詳細資訊
      When 使用 HistoricalExamImportService 匯入 20 題考古題
      Then 可透過 GET /api/v1/exam-import/exams/TEST/00/0000 查詢詳情
      And 回應應包含 total_questions, actual_questions, created_at 等欄位
