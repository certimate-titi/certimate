# language: zh-TW
@feature-34 @platform-subject-fork
功能: 預載科目解耦式 Fork 模型
  為了 讓用戶快速起步又能自主管理學習材料
  作為 考生與平台管理員
  我想要 選平台預載科目時一次性複製資源與心智圖，之後完全解耦；平台 admin 可草稿/發布/回滾

  背景:
    假設 資料庫已套用 migration 065
    並且 存在平台管理員帳號 "admin@certimate.app"
    並且 存在考生帳號 "alice@test.com"
    並且 存在 scope=platform 的科目 "iPAS AI 應用規劃師（初級）" 綁定 3 份預載 PDF 資源

  @US-01 @fork
  場景: 用戶選平台預載科目觸發一次性 Fork
    假設 我以 "alice@test.com" 身份登入
    當 我呼叫 POST "/api/v1/subjects/{platform_subject_id}/fork-from-platform"
    那麼 回應狀態碼應為 201
    並且 回傳欄位 "user_subject_id" 是新建立的 scope=personal 科目
    並且 該 user subject 擁有 3 份 scope=personal 的 resources（複製自 platform）
    並且 該 user subject 擁有對應的 knowledge_nodes（source_resource_count = 1）
    並且 GCS 已有 3 份複製的檔案（不與 platform 原檔共用路徑）

  @US-01 @idempotency
  場景: 同一用戶重複 fork 同一平台科目應被拒絕
    假設 我以 "alice@test.com" 身份登入
    並且 我已 fork 過 "iPAS AI 應用規劃師（初級）"
    當 我再次呼叫 POST "/api/v1/subjects/{platform_subject_id}/fork-from-platform"
    那麼 回應狀態碼應為 409
    並且 錯誤訊息包含 "您已擁有此科目"

  @US-01 @atomicity
  場景: Fork 過程 GCS 複製失敗應完整 rollback
    假設 我以 "alice@test.com" 身份登入
    並且 GCS copy_blob 在第 2 份檔案模擬失敗
    當 我呼叫 POST "/api/v1/subjects/{platform_subject_id}/fork-from-platform"
    那麼 回應狀態碼應為 500
    並且 資料庫中沒有新增任何屬於 "alice@test.com" 的 subject/resources/nodes
    並且 GCS 中沒有殘留的半複製檔案（第 1 份已複製的檔案已清除）

  @US-02 @cascade-delete
  場景: 用戶刪除資源連帶移除該資源專屬節點
    假設 我以 "alice@test.com" 身份登入
    並且 我已 fork "iPAS AI 應用規劃師（初級）"
    並且 我的科目中有資源 R1 對應 5 個專屬節點（source_resource_count = 1）
    當 我呼叫 DELETE "/api/v1/resources/{R1_id}"
    那麼 回應狀態碼應為 200
    並且 該 5 個節點已從 knowledge_nodes 刪除
    並且 該科目心智圖回應不再包含這些節點

  @US-02 @merged-node @ignore
  # TODO: merged node decrement 需 schema 改造（resource_id 改為 join 表或可為 NULL）
  場景: 刪除資源時 merged 節點僅減少引用計數
    假設 我以 "alice@test.com" 身份登入
    並且 節點 N1 被資源 R1 與 R2 共同引用（source_resource_count = 2）
    當 我呼叫 DELETE "/api/v1/resources/{R1_id}"
    那麼 節點 N1 仍存在
    並且 節點 N1 的 source_resource_count = 1

  @US-02 @empty-state
  場景: 刪光所有資源後心智圖為合法空態
    假設 我以 "alice@test.com" 身份登入
    並且 我已 fork "iPAS AI 應用規劃師（初級）" 並刪除全部 3 份資源
    當 我呼叫 GET "/api/v1/knowledge-map/subjects/{user_subject_id}/nodes"
    那麼 回應狀態碼應為 200
    並且 回傳 "nodes" 為空陣列
    並且 回傳 "empty_reason" 為 "no_resources"

  @US-03 @admin-draft
  場景: 平台管理員編輯預載科目草稿不影響現有用戶
    假設 我以 "admin@certimate.app" 身份登入
    並且 "alice@test.com" 已 fork "iPAS AI 應用規劃師（初級）"（版本 v1）
    當 我呼叫 PUT "/api/v1/admin/platform-subjects/{id}/draft" 修改資源清單
    那麼 回應狀態碼應為 200
    並且 "alice@test.com" 查詢其科目資源時內容不變

  @US-03 @admin-publish
  場景: 平台管理員發布新版後僅影響未來選科用戶
    假設 我以 "admin@certimate.app" 身份登入
    並且 "alice@test.com" 已 fork "iPAS AI 應用規劃師（初級）"（版本 v1）
    並且 platform subject 版本為 v1，已有草稿修改
    當 我呼叫 POST "/api/v1/admin/platform-subjects/{id}/publish"
    那麼 回應狀態碼應為 200
    並且 該 subject 的 version 為 2，published_at 已更新
    並且 先前已 fork 的 "alice@test.com" 的科目內容不變
    當 考生 "bob@test.com" 接著 fork 同一 platform subject
    那麼 bob 取得的是 v2 的資源與節點

  @US-03 @admin-rollback
  場景: 平台管理員可回滾至前一版本
    假設 我以 "admin@certimate.app" 身份登入
    並且 platform subject 已發布 v1 → v2
    當 我呼叫 POST "/api/v1/admin/platform-subjects/{id}/rollback"
    那麼 回應狀態碼應為 200
    並且 subject 的 version 恢復為 1
    並且 後續 fork 的用戶取得的是 v1 內容
