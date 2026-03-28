# RAG Pipeline 實作計畫：CertiMate AI 文件處理與考題生成

## Context

CertiMate 需要實作完整的 RAG (Retrieval-Augmented Generation) 管線，讓使用者上傳的 PDF/Markdown 文件能被 AI 解析、切塊、向量化，並用於智慧考題生成與 AI 教練問答。目前後端已有完整的資源上傳驗證、4 階段考題生成框架（mock 資料）、知識節點結構，但缺乏真實的 LLM 整合與向量搜尋。

**技術決策：**
- **LLM**: Claude (Anthropic API) — 同時用於 PDF 解析（原生支援 PDF 輸入）
- **向量資料庫**: pgvector（PostgreSQL 擴充，不需額外服務）
- **Embedding**: Voyage AI（Anthropic 推薦的 embedding 夥伴，voyage-3 模型）
- **範圍**: 一次到位的完整 RAG pipeline

---

## Phase 1：基礎設施 — 依賴與設定

### 1.1 新增 Python 依賴
**檔案**: `backend/requirements.txt`

```
anthropic>=0.40.0      # Claude API client（PDF 輸入、chat completions）
voyageai>=0.3.0        # Voyage AI embedding client
pgvector>=0.3.0        # SQLAlchemy pgvector 整合
tiktoken>=0.7.0        # Token 計數（chunk 大小管理）
```

### 1.2 更新設定
**檔案**: `backend/app/core/config.py`

新增環境變數：
| 變數 | 預設值 | 說明 |
|------|--------|------|
| `ANTHROPIC_API_KEY` | (必填) | Claude API 金鑰 |
| `VOYAGE_API_KEY` | (必填) | Voyage AI 金鑰 |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | 生成用模型 |
| `CLAUDE_PDF_MODEL` | `claude-sonnet-4-20250514` | PDF 解析用模型 |
| `VOYAGE_EMBED_MODEL` | `voyage-3` | Embedding 模型（1024 維） |
| `CHUNK_SIZE_TOKENS` | `512` | chunk 目標大小 |
| `CHUNK_OVERLAP_TOKENS` | `64` | chunk 重疊量 |
| `RETRIEVAL_TOP_K` | `10` | 向量搜尋回傳數量 |

---

## Phase 2：資料庫 — pgvector + resource_chunks 表

### 2.1 Alembic Migration 018
**檔案**: `backend/alembic/versions/018_create_resource_chunks_table.py`

```sql
-- 啟用 pgvector 擴充
CREATE EXTENSION IF NOT EXISTS vector;

-- 建立 resource_chunks 表
CREATE TABLE resource_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resource_id UUID NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
  node_id UUID REFERENCES knowledge_nodes(id) ON DELETE SET NULL,
  chunk_index INTEGER NOT NULL,
  content TEXT NOT NULL,
  token_count INTEGER NOT NULL,
  source_page_start INTEGER,
  source_page_end INTEGER,
  metadata_json JSON,
  embedding vector(1024),  -- Voyage AI voyage-3 輸出維度
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 向量搜尋索引（IVFFlat，適合初期規模）
CREATE INDEX idx_chunks_embedding ON resource_chunks
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 加速按 resource_id 查詢
CREATE INDEX idx_chunks_resource_id ON resource_chunks(resource_id);
```

### 2.2 ORM 模型
**新增**: `backend/app/models/resource_chunk.py`

```python
class ResourceChunk(Base):
    __tablename__ = "resource_chunks"
    id            # UUID PK
    resource_id   # FK → resources.id
    node_id       # FK → knowledge_nodes.id (nullable)
    chunk_index   # int
    content       # text
    token_count   # int
    source_page_start  # int (nullable)
    source_page_end    # int (nullable)
    metadata_json      # JSON (nullable)
    embedding          # Vector(1024)
    created_at         # datetime
```

### 2.3 更新 DBML（SSOT）
**檔案**: `project/specs/entity/erm.dbml` — 新增 `resource_chunks` 表定義

### 2.4 註冊模型
**檔案**: `backend/app/models/__init__.py` — import ResourceChunk

---

## Phase 3：Repository 層

### 3.1 ResourceChunkRepository
**新增**: `backend/app/repositories/resource_chunk_repository.py`

| 方法 | 說明 |
|------|------|
| `save_batch(chunks)` | 批量 insert（caller 控制 commit） |
| `find_by_resource_id(resource_id)` | 按 chunk_index 排序 |
| `delete_by_resource_id(resource_id)` | 重新處理時清除舊 chunks |
| `search_similar(embedding, resource_ids, top_k)` | **核心**：pgvector cosine 距離搜尋，限定 resource_ids 範圍（安全邊界：使用者只能搜尋自己的文件） |

---

## Phase 4：服務層 — 4 個新 Service

### 4.1 EmbeddingService
**新增**: `backend/app/services/embedding_service.py`

- `embed_texts(texts, input_type="document")` — 批量 embedding（每次最多 128 筆）
- `embed_query(query)` — 單筆查詢 embedding（`input_type="query"`）
- Voyage AI 的非對稱 embedding（document vs query 不同 input_type）提升 Q&A 檢索品質

### 4.2 DocumentProcessingService ⭐ 最核心
**新增**: `backend/app/services/document_processing_service.py`

處理流程：`process_resource(resource_id)` →

```
1. 標記 Resource → PROCESSING
2. 依類型提取文字：
   ├─ PDF  → Claude API（原生 PDF 輸入，type: "document"）
   ├─ Markdown/TXT → 直接讀取，按 # 標題切段
   └─ Image → Claude Vision OCR
3. 建立 knowledge_nodes 階層（root + 各章節子節點）
4. 語意切塊（tiktoken 計數，512 tokens/chunk，64 overlap）
5. Voyage AI 批量 embedding（每批 64 筆）
6. 儲存 ResourceChunk（含 embedding 向量）
7. 標記 Resource → COMPLETED
   （失敗 → FAILED + error_message）
```

### 4.3 RetrievalService
**新增**: `backend/app/services/retrieval_service.py`

- `retrieve(query, resource_ids, top_k)` — 查詢 embedding → 向量搜尋 → 回傳相關 chunks
- `build_context_string(chunks, max_tokens=4000)` — 組裝 RAG context 字串（含頁碼引用）

### 4.4 ClaudeService
**新增**: `backend/app/services/claude_service.py`

- `generate_with_context(system_prompt, user_prompt, context, max_tokens)` — RAG 生成
- `generate_simple(system_prompt, user_prompt, max_tokens)` — 無 RAG 生成

---

## Phase 5：整合現有服務

### 5.1 重構 AiGenerationService（最高風險變更）
**修改**: `backend/app/services/ai_generation_service.py`

- 注入 `RetrievalService` + `ClaudeService`
- 4 階段從 mock 改為真實 Claude API 呼叫：
  - Stage 1（考點分析）：RAG context + prompt template → Claude
  - Stage 2（考題生成）：RAG context + user context（age, education, career）→ Claude
  - Stage 3（干擾項優化）：Stage 2 輸出 + user context → Claude
  - Stage 4（格式化輸出）：JSON schema 驗證 → Claude
- **安全網**：每個 stage 若 API 失敗，fallback 到現有 mock 邏輯（漸進式上線）

### 5.2 新增處理 API 端點
**修改**: `backend/app/api/resource.py`

```
POST /resources/{resource_id}/process
  → BackgroundTasks 非同步呼叫 DocumentProcessingService
  → 立即回傳 {"status": "processing"}
```

### 5.3 AI 教練整合（選做）
**修改**: `backend/app/services/wrong_answer_service.py`

新增 `ask_ai_coach(question_id, user_id, user_question)` → 用 RAG 取得相關文件段落 → Claude 生成教練回答

---

## Phase 6：測試

### 6.1 更新 Testcontainer
**修改**: `backend/tests/features/environment.py`

```python
# 從 postgres:15 改為 pgvector/pgvector:pg15
image="pgvector/pgvector:pg15"
```

### 6.2 BDD Feature
**新增**: `backend/tests/features/02a-RAG文件處理.feature`

覆蓋場景：上傳 PDF → 處理 → chunks 建立、向量搜尋相關性、重新處理清除舊 chunks

### 6.3 Mock 外部 API
測試中 mock `anthropic.Anthropic` 和 `voyageai.Client`，回傳確定性結果

---

## 實作順序（7 個 Checkpoint）

| # | Checkpoint | 涵蓋步驟 | 驗證方式 |
|---|-----------|---------|---------|
| 1 | DB 基礎 | requirements, config, migration 018, model, DBML | `alembic upgrade head` 成功 |
| 2 | Embed + 儲存 | ChunkRepository, EmbeddingService | 手動 embed 字串 → 儲存 → 查詢 vector |
| 3 | 文件處理 | DocumentProcessingService, process endpoint | 上傳小 PDF → 呼叫 process → DB 有 chunks |
| 4 | 向量檢索 | RetrievalService, ClaudeService | 查詢已處理文件 → 回傳相關 chunks |
| 5 | 考題生成 | 重構 AiGenerationService | 對已處理文件生成考題 → 真實 AI 考題 |
| 6 | AI 教練 | WrongAnswerService 整合 | 問教練問題 → 文件根據的回答 |
| 7 | BDD 測試 | Feature file + step definitions + mocks | `behave` 全部通過 |

---

## 關鍵檔案清單

| 檔案 | 動作 |
|------|------|
| `backend/requirements.txt` | 修改：加 anthropic, voyageai, pgvector, tiktoken |
| `backend/app/core/config.py` | 修改：加 AI/RAG 設定 |
| `backend/alembic/versions/018_create_resource_chunks_table.py` | **新增**：pgvector + resource_chunks |
| `backend/app/models/resource_chunk.py` | **新增**：ResourceChunk ORM |
| `backend/app/models/__init__.py` | 修改：註冊新 model |
| `backend/app/repositories/resource_chunk_repository.py` | **新增**：向量搜尋 repository |
| `backend/app/services/embedding_service.py` | **新增**：Voyage AI wrapper |
| `backend/app/services/document_processing_service.py` | **新增**：文件處理 pipeline |
| `backend/app/services/retrieval_service.py` | **新增**：RAG 檢索 |
| `backend/app/services/claude_service.py` | **新增**：Claude API wrapper |
| `backend/app/services/ai_generation_service.py` | 修改：mock → 真實 Claude + RAG |
| `backend/app/api/resource.py` | 修改：加 POST /resources/{id}/process |
| `project/specs/entity/erm.dbml` | 修改：加 resource_chunks 表 |
| `backend/tests/features/environment.py` | 修改：pgvector Docker image |
