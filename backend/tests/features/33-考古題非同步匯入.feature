Feature: 考古題非同步匯入 (Phase 3: Async Background Processing)
  # 背景工作、任務追蹤、品質閘門、審計日誌、監控儀表板、匯入復原

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 | 角色      |
      | admin     | admin@example.com  | ULTRA    | 平台管理員 |
      | user1     | user1@example.com  | PRO_199    | 一般使用者 |
    And APScheduler 已初始化
    And 非同步背景工作 (ImportBackgroundWorker) 已啟動

  Rule: 非同步匯入提交 (Async Import Submission)

    Example: 提交非同步匯入任務
      When user1 POST /api/v1/exam-import/async
        | 欄位 | 值 |
        | question_pdf | normal_questions.pdf |
        | answer_pdf | normal_answers.pdf |
        | exam_code | P |
        | category_code | 01 |
        | subject_code | 0101 |
      Then HTTP 狀態碼應為 200
      And 回應應包含：
        | 欄位 | 預期值 |
        | task_id | 非空 UUID |
        | status | "pending" |
        | message | 包含 "queued" |
      And ImportTask 應被建立在資料庫，狀態為 "pending"
      And APScheduler 應有新工作已排隊

    Example: 立即開始背景處理
      When user1 提交非同步匯入，等待背景工作啟動
      And 等待 2 秒讓 APScheduler 処理
      Then ImportTask 狀態應轉換為 "processing"
      And ImportTask.started_at 應被設定

  Rule: 任務狀態追蹤 (Task Status Tracking)

    Example: 查詢任務狀態
      Given user1 已提交非同步匯入 task_id=abc123
      When user1 GET /api/v1/exam-import/tasks/abc123
      Then HTTP 狀態碼應為 200
      And 回應應包含：
        | 欄位 | 含義 |
        | task_id | 任務 ID |
        | status | 當前狀態 (pending/processing/validating/importing/completed/failed) |
        | progress_percent | 進度 (0-100) |
        | questions_processed | 已處理題數 |
        | questions_valid | 有效題數 |
        | questions_imported | 已匯入題數 |
        | error_message | 如失敗則顯示錯誤 |

    Example: 實時進度更新
      When 背景工作正在處理
      And 系統每秒更新 progress_percent
      Then 連續查詢 progress_percent 應逐漸增加
      And 最終到達 100% 或失敗

    Example: 取消進行中的任務
      Given user1 有 task_id=abc123 在 "processing" 狀態
      When user1 POST /api/v1/exam-import/tasks/abc123/cancel
      Then HTTP 狀態碼應為 200
      And ImportTask 狀態應變為 "cancelled"
      And APScheduler 應取消該工作

  Rule: 任務生命週期 (Task Lifecycle)

    Example: 完整成功流程 (PENDING → PROCESSING → VALIDATING → IMPORTING → COMPLETED)
      When 背景工作處理完整的有效 PDF
      Then 狀態轉換應依序進行：
        | 從 | 到 | 條件 |
        | pending | processing | 工作開始 |
        | processing | validating | 提取完成 |
        | validating | importing | 驗證通過 |
        | importing | completed | 匯入成功 |
      And 每個階段應有對應的 audit log 條目
      And progress_percent 應逐步更新 (5 → 25 → 40 → 50 → 100)

    Example: 驗證失敗流程 (VALIDATING → FAILED)
      When 背景工作遇到驗證閘門失敗
      Then 狀態應轉換為 "failed"
      And ImportTask.requires_manual_review 應為 true
      And error_message 應說明失敗原因
      And validation_errors 應記錄詳細錯誤

    Example: 失敗並自動重試
      Given ImportTask 狀態為 "failed"，retry_count=0
      When 系統嘗試重試
      Then retry_count 應遞增至 1
      And 狀態應重設為 "pending"
      And 再次被排隊進行背景處理

  Rule: 品質閘門 (Quality Gates)

    Example: Gate 1 - PDF 文件驗證
      When 背景工作接收 PDF 檔案
      Then 應驗證：
        | 檢查 | 標準 |
        | 檔案存在 | 必須存在 |
        | 檔案大小 | 1KB - 50MB |
        | PDF 格式有效 | PyPDF2 可讀 |
        | 頁數 | ≥1, ≤500 |
        | 可提取文本 | 前 5 頁至少有一頁有文本 |

    Example: Gate 2 - PDF 配對驗證
      When 背景工作驗證試題 PDF 和答案 PDF
      Then 應檢查：
        | 項目 | 規則 |
        | 兩者都有效 | 都必須通過 Gate 1 |
        | 試題頁數 ≥ 答案頁數 | 邏輯驗證 |
        | 檔案大小比率 | 不超過 5:1 |

    Example: Gate 3 - 腐敗偵測
      When 背景工作掃描 PDF 結構問題
      Then 應識別：
        | 問題 | 風險等級 |
        | PDF 加密 | 中等 |
        | 頁面提取失敗 | 中等/高 |
        | 結構錯誤 | 高 |
      And 高風險應設定 requires_manual_review=true

    Example: Gate 4 - 難度評估
      When 背景工作估計 PDF 難度
      Then 應計算：
        | 因素 | 權重 |
        | 頁數 | 每 50 頁 +1 |
        | 檔案大小 | >10MB +1 |
        | 影像 PDF | +2 |
        | 結構問題 | +1-2 |
      And 返回 difficulty_score (1-5) 與 estimated_time_seconds

  Rule: 審計日誌 (Audit Logging)

    Example: 每個階段建立審計條目
      When 背景工作進行各個階段
      Then 應自動建立 ImportAuditLog 條目：
        | 事件 | 何時 | 記錄內容 |
        | task_created | 提交時 | task_id, user_id, exam_code |
        | task_started | 工作開始 | started_at |
        | extraction_started | 提取開始 | PDF 路徑 |
        | extraction_complete | 提取完成 | questions_processed, questions_valid |
        | validation_complete | 驗證完成 | critical_errors, can_proceed |
        | import_complete | 匯入完成 | questions_imported, duration_ms |
        | task_completed | 任務結束 | final_status |

    Example: 失敗事件審計
      When 背景工作失敗
      Then ImportAuditLog 應記錄：
        | 欄位 | 值 |
        | action | task_failed |
        | status | failed |
        | error_code | 故障代碼 |
        | error_message | 故障訊息 |

    # TODO: 審計日誌查詢 API 將在 Phase 3.1 實現
    # 服務層已完整實現：ImportAuditLogService.search_audit_logs()
    # Example: 搜尋審計日誌
    #   When user1 GET /api/v1/exam-import/audit?exam_code=P&status=completed
    #   Then 應返回符合篩選條件的所有事件
    #   And 按 created_at 倒序排列

  Rule: 監控儀表板 (Monitoring Dashboard)

    Example: 取得整體統計
      When admin GET /api/v1/exam-import/dashboard/stats
      Then 回應應包含：
        | 項目 | 內容 |
        | total_jobs | 總任務數 |
        | in_progress | 進行中數 |
        | completed | 已完成數 |
        | failed | 失敗數 |
        | success_rate | 成功率 (%) |
        | average_duration_seconds | 平均耗時 |
        | total_questions_imported | 總匯入題數 |

    Example: 檢視失敗任務列表
      When admin GET /api/v1/exam-import/dashboard/failed-jobs
      Then 應返回失敗任務清單，包含：
        | 欄位 | 說明 |
        | task_id | 任務 ID |
        | error_message | 失敗原因 |
        | retry_count | 已重試次數 |
        | can_retry | 是否可再試 (retry_count < 3) |

    Example: 檢視最近的任務
      When admin GET /api/v1/exam-import/dashboard/recent-jobs?limit=20
      Then 應按最後更新時間倒序返回 20 個任務

    Example: 效能指標 (過去 7 天)
      When admin GET /api/v1/exam-import/dashboard/performance-metrics?days=7
      Then 回應應包含：
        | 指標 | 說明 |
        | total_jobs | 這段期間的工作數 |
        | success_rate | 成功率 |
        | average_duration_seconds | 平均完成時間 |

    Example: 任務詳細資訊
      When admin GET /api/v1/exam-import/dashboard/job-details/{task_id}
      Then 回應應包含：
        | 部分 | 內容 |
        | task | 基本信息 |
        | statistics | 統計數據 |
        | timeline | 時間線 |
        | quality | 品質信息 |
        | error | 錯誤詳情 |
        | audit_trail | 完整審計追蹤 |

  # TODO: 匯入復原 API 路由將在 Phase 3.1 實現
  # 服務層已完整實現：ImportRollbackService
  #   - can_rollback(): 檢查復原可用性
  #   - rollback_import(): 執行匯入復原
  #   - get_rollback_history(): 復原歷史記錄

  # Rule: 匯入復原 (Rollback & Undo)
  #
  #   Example: 檢查復原可用性
  #     Given user1 已完成匯入，產生 HistoricalExam
  #     When admin GET /api/v1/exam-import/rollback/{task_id}/can-rollback
  #     Then 回應應包含：
  #       | 欄位 | 預期值 |
  #       | can_rollback | true |
  #       | reason | "Rollback is available" |
  #       | task_details | exam_code, questions_imported 等 |
  #
  #   Example: 執行匯入復原
  #     Given user1 匯入了 50 題，exam_id=xyz789
  #     When admin POST /api/v1/exam-import/rollback/{task_id}
  #       | 參數 | 值 |
  #       | reason | "Duplicate import detected" |
  #     Then HTTP 狀態碼應為 200
  #     And Question 應有 50 筆被刪除（WHERE historical_exam_id=xyz789）
  #     And HistoricalExam (xyz789) 應被刪除
  #     And ImportTask 狀態應變為 "cancelled"
  #     And ImportAuditLog 應記錄 "import_rolled_back" 事件
  #     And 原始使用者 user1 應收通知
  #
  #   Example: 復原歷史記錄
  #     When admin GET /api/v1/exam-import/rollback/history
  #     Then 應返回所有復原操作
  #     And 包含 rolled_back_by, reason, questions_deleted, rolled_back_at

  # TODO: Webhook 通知功能將在 Phase 4 實現
  # 服務層已完整實現：ImportWebhookService
  #   - 支援 6 個事件類型
  #   - 非同步發送
  #   - 自動重試機制（最多 3 次）

  # Rule: Webhook 通知 (Event Notifications)
  #
  #   Example: 配置 Webhook URL
  #     When admin 設定 webhook_url = "https://example.com/webhooks/import"
  #     Then 系統應在事件發生時發送 POST
  #
  #   Example: 任務建立事件
  #     When user1 提交非同步匯入
  #     Then 系統應 POST 至 webhook：
  #       ```json
  #       {
  #         "event": "import.task.created",
  #         "timestamp": "2026-04-10T...",
  #         "data": {
  #           "task_id": "...",
  #           "exam_code": "P",
  #           "category_code": "01",
  #           "subject_code": "0101"
  #         }
  #       }
  #       ```
  #
  #   Example: 完成事件
  #     When 背景工作完成匯入
  #     Then 系統應 POST：
  #       ```json
  #       {
  #         "event": "import.completed",
  #         "data": {
  #           "task_id": "...",
  #           "historical_exam_id": "...",
  #           "questions_imported": 50,
  #           "duration_ms": 45000
  #         }
  #       }
  #       ```
  #
  #   Example: 失敗事件
  #     When 背景工作失敗
  #     Then 系統應 POST：
  #       ```json
  #       {
  #         "event": "import.failed",
  #         "data": {
  #           "task_id": "...",
  #           "error_message": "...",
  #           "retry_count": 0
  #         }
  #       }
  #       ```
  #
  #   Example: Webhook 失敗重試
  #     When webhook endpoint 返回 500
  #     Then 系統應重試最多 3 次，間隔遞增

  Rule: 錯誤處理與回復 (Error Handling & Recovery)

    Example: PDF 檔案不可讀
      When 背景工作收到損毀的 PDF
      Then ImportTask.status 應為 "failed"
      And error_message 應為 "Invalid PDF format: ..."
      And 系統應自動重試 (retry_count ≤ 3)

    Example: 資料庫連線失敗
      When 背景工作在匯入階段失去連線
      Then ImportTask 應標記為 "failed"
      And 工作應在隊列中重新排隊
      And 不應丟失已處理的進度

    Example: 超時處理
      When 背景工作超過 30 分鐘未完成
      Then 系統應設定 requires_manual_review=true
      And 標記為 "failed" 或 "pending_review"

  Rule: 效能與可擴展性 (Performance & Scalability)

    Example: 並行處理多個匯入
      When 5 個使用者同時提交匯入
      Then APScheduler 應有 5 個工作在隊列中
      And ThreadPoolExecutor (max_workers=5) 應並行處理
      And 每個工作應獨立進行，不相互影響

    Example: 長期執行的任務
      When 背景工作處理 500 頁的大型 PDF
      Then progress_percent 應持續更新（每 10 秒）
      And 不應鎖定或阻止其他任務

    Example: 清理舊任務
      When 系統在午夜運行清理工作
      Then 應刪除 30 天以上的已完成/失敗任務
      And 保留最近 30 天的審計日誌
