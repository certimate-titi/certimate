@backend
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

  Rule: 重複匯入處理 (Duplicate Import Handling)

    # 設計：預設重新匯入會覆蓋（update）既存記錄；如要安全略過請帶 skip_existing=true
    Example: 重複匯入同一份考古題應更新既存記錄
      Given 系統中已匯入考古題：TEST/00/0000
      When 重新匯入同一份考古題（skip_existing=false）
      Then 重複匯入應成功更新既存 HistoricalExam（不新增新記錄）
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
