@feature_45 @chk_depth_range @migration_091 @backend
Feature: knowledge_nodes depth CHECK 寫入相容性（後端契約）
  覆蓋 migration 091 chk_depth_range CHECK (depth BETWEEN 1 AND 3) 對所有
  KnowledgeNode 寫入端的相容性驗證。

  歷史背景：2026-05-10 production 全量上傳失敗 — Sprint 10 加 migration 091
  但只修 document_processing_service，knowledge_map / onboarding / merge 三個
  service 仍寫 depth=0，下個寫入即觸發 CHECK 違規。

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"

  @backend
  Rule: ORM KnowledgeNode 預設 depth
    Scenario: 不指定 depth 建 KnowledgeNode 預設值 ≥ 1
      Given 用戶 "alice@example.com" 擁有資源 "res-45" 解析狀態為 "success"
      When 建立 KnowledgeNode(resource_id=res-45, name="root", parent_id=NULL)（不指定 depth）
      Then KnowledgeNode 寫入成功
      And 該節點 depth 為 1

  @backend
  Rule: KnowledgeMapService 建 root 節點
    Scenario: build_for_resource 建出的 root 深度為 1
      Given 用戶 "alice@example.com" 擁有資源 "map-res" 解析狀態為 "success"
      When 呼叫 KnowledgeMapService.build_for_resource("map-res")
      Then 該 root 節點 depth 為 1
      And 寫入 DB 不觸發 chk_depth_range CHECK 違規

  @backend
  Rule: KnowledgeMergeService keep_separate
    Scenario: merge 衝突選擇 keep_separate 時新節點 depth 為 1
      Given 一筆 MergeConflict pending 等待 alice 決策
      When 用戶 alice 對該衝突 POST decision={"action":"keep_separate"}
      Then 新節點 depth 為 1
      And 寫入 DB 不觸發 chk_depth_range CHECK 違規
