# TiTi 上傳資料 → 考題生成 技術文件

> **版本**：v2.0 | 2026-04-03
> **對應 Feature**：02-資源上傳、03-知識心智圖、04-測驗設定、04a-AI考題生成、23-考古題題庫管理

---

## 全景流程圖

```
使用者上傳 PDF / Markdown / YouTube / 手寫圖片
          │
    ┌─────▼──────────────────────────────────────┐
    │  Stage A：資源接收                          │
    │  POST /resources/upload                     │
    │  → Resource record (status=PENDING)         │
    └─────┬──────────────────────────────────────┘
          │ 背景非同步處理（Pipeline B 全自動）
    ┌─────▼──────────────────────────────────────┐
    │  Stage A.5：內容類型偵測（Stage 0）          │
    │  Gemini Flash 分析前 3 頁                   │
    │  → content_type = 7 種之一                  │
    │  exam | regulation | textbook | summary     │
    │  formula | syllabus | general               │
    └─────┬──────────────────────────────────────┘
          │ 依 content_type 分流
    ┌─────▼──────────────────────────────────────┐
    │  Stage B：文件處理 Pipeline                  │
    │  依 content_type 選擇對應 Prompt：           │
    │  exam       → 題目結構化提取                 │
    │  regulation → 法規條文提取                   │
    │  textbook   → 概念章節提取                   │
    │  summary    → 要點閃卡提取                   │
    │  formula    → KaTeX 公式辨識                 │
    │  syllabus   → 考試大綱主題提取               │
    │  general    → 基礎文字結構化                  │
    │  → 4 層品質驗證 → Resource status=COMPLETED  │
    └─────┬──────────────────────────────────────┘
          │
    ┌─────▼──────────────────────────────────────┐
    │  Stage C：知識心智圖 / 題庫（依類型）        │
    │  exam     → question 表（直接可練習）        │
    │  regulation → knowledge_node（法規庫）       │
    │  textbook → knowledge_node（心智圖）         │
    │  summary  → flashcard（閃卡集）              │
    │  formula  → knowledge_node（公式卡）         │
    │  syllabus → study_plan（學習路徑）           │
    │  general  → 純文字儲存                       │
    └─────┬──────────────────────────────────────┘
          │ 使用者點擊「生成模擬考」
    ┌─────▼──────────────────────────────────────┐
    │  Stage D：混合式出題引擎 v2.0               │
    │  四層 Pipeline:                              │
    │  Layer -1: 模式判定（衝刺/標準/精熟）        │
    │  Layer  0: 弱點+記憶+信心度分析              │
    │  Layer  1: 配比計算                          │
    │  Layer  2: 20%考古🟢 + 80%AI🟡 + 交錯排列    │
    │  素材來源：question + knowledge_node +        │
    │           flashcard + formula（跨類型）       │
    └─────┬──────────────────────────────────────┘
          │
    ┌─────▼──────────────────────────────────────┐
    │  Stage E：考卷呈現                          │
    │  /exam/workspace 作答介面                    │
    │  作答完成 → 更新 node_mastery + SM-2         │
    └────────────────────────────────────────────┘
```

---

## 內容類型分類（ContentType）

### 兩維度設計

```
維度 1：檔案格式（ResourceType） — 由副檔名決定
  pdf | markdown | txt | image | youtube

維度 2：內容類型（ContentType） — 由 Stage 0 LLM 偵測
  exam | regulation | textbook | summary | formula | syllabus | general
```

### 7 種內容類型

| ContentType | 中文 | 來源範例 | 處理策略 | 產出物 |
|-------------|------|---------|---------|--------|
| **exam** | 考試試卷 | 考古題、模擬考、練習題 | 結構化提取（題幹+選項+答案+Bloom） | 題庫 → 直接練習 |
| **regulation** | 法規規範 | 金管會法規、證交法 | 條文提取（條號+內容+關鍵詞） | 法規知識庫 → AI 法規出題 |
| **textbook** | 教材內容 | 教科書、參考書 | 概念提取（章節+定義+關聯） | 知識心智圖 → AI 概念出題 |
| **summary** | 重點整理 | 筆記、講義、衝刺整理 | 要點提取（關鍵詞+摘要） | 閃卡集 → 快速複習 |
| **formula** | 公式表 | 數學/財務/統計公式 | KaTeX 公式辨識 + 變數說明 | 公式卡 → 計算題生成 |
| **syllabus** | 考試大綱 | 官方考試範圍、簡章 | 主題提取（考科+權重） | 學習路徑規劃 |
| **general** | 一般文件 | 無法歸類的內容 | 基礎文字結構化 | 純文字 Markdown |

### Stage 0 偵測方式

- **引擎**：Gemini 2.5 Flash（thinking_budget=0）
- **成本**：~$0.001/次
- **速度**：~1-2 秒
- **輸入**：整份 PDF 原生上傳
- **輸出**：JSON（content_type + confidence + key_features）

### DB Schema 擴充

```sql
ALTER TABLE resource ADD COLUMN content_type VARCHAR(20) DEFAULT 'general';
-- enum: exam, regulation, textbook, summary, formula, syllabus, general
```

---

## Stage A：資源接收

### API

```
POST /api/v1/resources/upload
Content-Type: multipart/form-data

Body:
  file: binary
  subject_id: UUID
  filename: string
```

### 處理邏輯

1. 驗證使用者身份和訂閱配額
2. 建立 `resources` 記錄（status=PENDING）
3. 儲存原始檔案到 `uploads/{user_id}/{resource_id}.{ext}`
4. 回傳 resource_id，前端顯示「解析中...」

### DB 變更

| 表 | 操作 | 欄位 |
|----|------|------|
| `resources` | INSERT | id, user_id, subject_id, name, type, status=PENDING |

---

## Stage B：文件處理 Pipeline

### 10 步驟處理流程

位置：`backend/app/services/document_processing_service.py`

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ 0.版權檢查│ → │ 1.文字提取│ → │ 2.文字清理│ → │ 3.AI結構 │
│ 掃描關鍵字│   │ PDF/MD/  │   │ 去頁首尾  │   │ 章節階層 │
│           │   │ YT/Image │   │ 去頁碼    │   │ 分析     │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
      │              │              │              │
      ▼              ▼              ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ 4.刪舊資料│ → │ 5.建立   │ → │ 6.智慧切塊│ → │ 7.向量   │
│ chunks+  │   │ 知識節點 │   │ 段落→token│   │ 嵌入     │
│ nodes    │   │ depth0-3 │   │ 512token  │   │ Voyage   │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
      │              │              │              │
      ▼              ▼              ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│ 8.儲存   │ → │ 9.正規化 │ → │10.清理   │
│ chunks+  │   │ Markdown │   │ 原始檔案 │
│ embedding│   │ 重建標題 │   │ status=  │
│          │   │          │   │ COMPLETED│
└──────────┘   └──────────┘   └──────────┘
```

### 各步驟詳解

#### Step 0 — 版權檢查
- 掃描前 2 頁文字
- 偵測關鍵字：「授權嚴禁轉載」「版權所有」等
- 命中 → 拒絕處理（ValueError）

#### Step 1 — 文字提取

| 檔案類型 | 提取方式 | 產出 |
|---------|---------|------|
| PDF | PyMuPDF (fitz)，掃描頁 fallback Claude Vision | 每頁文字 + 頁碼 |
| Markdown/TXT | 標題語法 (#/##/###) 切分 | 章節 + depth 1-3 |
| 圖片 | Claude Vision OCR | 整份辨識文字 |
| YouTube | *(URL 處理，非檔案上傳)* | 字幕/摘要文字 |

產出格式：
```python
{
    "title": "文件標題",
    "sections": [
        {"page_num": 1, "content": "...", "depth": 1, "page_start": 1, "page_end": 3}
    ]
}
```

#### Step 2 — 文字清理
- 去除重複頁首/頁尾（出現 >50% 頁面的行）
- 去除頁碼
- 去除 PDF 特殊字元

#### Step 3 — AI 結構分析
- 輸入：前 40 頁文字摘要
- AI（Claude/Gemini）分析文件結構
- 產出：章節階層（depth 1-3）+ 頁碼範圍
```python
[
    {"title": "第一章 基礎概念", "depth": 1, "page_start": 1, "page_end": 15},
    {"title": "1.1 定義", "depth": 2, "page_start": 1, "page_end": 5},
]
```

#### Step 5 — 知識節點建立（關鍵步驟）

```
這是「上傳資料變成考題」的核心轉換點。
文件結構 → knowledge_nodes 樹 → 可選為測驗範圍。
```

| depth | 來源 | 範例 |
|-------|------|------|
| 0 | 根節點（資源標題） | "AWS SAA 講義 知識總覽" |
| 1 | 章級標題 | "第一章 EC2 運算服務" |
| 2 | 節級標題 | "1.1 EC2 實例類型" |
| 3 | 小節 | "1.1.1 Spot 實例定價" |

DB：
```sql
INSERT INTO knowledge_nodes (id, resource_id, parent_id, name, depth, sort_order, source_text)
VALUES (uuid, resource_id, parent_uuid, '章節名', 1, 0, '前500字內容');
```

#### Step 6 — 智慧切塊

```
切塊策略（由粗到細）：
  1. 章節邊界切分（優先）
  2. 段落切分（雙換行）
  3. Token 滑動視窗（最後手段）

參數：
  CHUNK_SIZE_TOKENS = 512
  CHUNK_OVERLAP_TOKENS = 128
```

每個 chunk 關聯到所屬的 knowledge_node（by section_title + depth 映射）。

#### Step 7 — 向量嵌入

```python
EmbeddingService.embed_texts(chunk_contents)
→ Voyage AI → 1024 維向量
→ 存入 resource_chunks.embedding (pgvector)
```

#### Step 8 — 儲存 chunks

```sql
INSERT INTO resource_chunks (id, resource_id, node_id, chunk_index, content, token_count, embedding)
VALUES (uuid, resource_id, node_uuid, 0, '文字內容...', 456, '[0.01, -0.02, ...]');
```

---

## Stage C：知識心智圖

### API

```
GET /api/v1/knowledge-map/subjects/{subjectId}/nodes
```

### 回傳

```json
{
    "resources": [{"id": "uuid", "name": "AWS SAA 講義", "type": "pdf"}],
    "nodes": [
        {
            "id": "uuid",
            "name": "AWS SAA 講義 知識總覽",
            "depth": 0,
            "available_questions": 0,
            "mastery_rate": 0,
            "color": "gray",
            "children": [
                {
                    "id": "uuid",
                    "name": "EC2 運算服務",
                    "depth": 1,
                    "available_questions": 20,
                    "children": []
                }
            ]
        }
    ]
}
```

前端渲染為互動心智圖，使用者可點選節點查看原文。

---

## Stage D：混合式出題引擎

*詳見 `exam-generation-spec.md` v2.0*

### 與上傳資料的關係

```
knowledge_nodes（來自上傳資料）
         │
         ├─ node.source_text → AI 出題時的上下文
         │
         ├─ resource_chunks.embedding → RAG 語意檢索
         │    └─ 查詢相關 chunks 作為出題 context
         │
         └─ node.available_questions → 配額計算
              └─ 考古題數 + 上傳資料可生成量
```

### AI 出題如何使用上傳資料

```python
# _generate_ai_for_node() 內部流程：

1. 查詢該 node 的 resource_chunks（向量語意搜尋）
   → RAG context（最相關的 2000 token）

2. 查詢該 node 的考古題（作為 few-shot 範例）
   → 3-5 題考古題完整內容

3. 組合 Prompt：
   System: "你是專業出題老師"
   User:
     [考古題範例]        ← 確保出題風格一致
     [上傳資料 RAG]      ← 確保考點來自教材
     [Bloom 目標]        ← 確保認知層次分佈
     [難度分佈]          ← 確保難度適配弱點

4. LLM 回傳 JSON array of questions
```

---

## Stage E：考卷作答後的回饋迴圈

```
使用者作答完成
      │
      ├─ UPDATE node_mastery
      │    mastery_rate = correct_count / total_count * 100
      │    color = green(≥80) / orange(60-79) / red(<60)
      │
      ├─ UPDATE question_stats
      │    ease_factor 調整（SM-2 演算法）
      │    next_review_date 計算
      │
      └─ INSERT answers
           selected_answer, is_correct, confidence
           → 下次出題時 Layer 0 會讀取這些資料
```

這形成一個**自適應學習迴圈**：

```
上傳教材 → 知識節點 → 出題（弱點導向）→ 作答 → 更新掌握度 → 下次出題更精準
                                        ↑                                    │
                                        └────────────────────────────────────┘
```

---

## DB 表關係圖

```
resources ──┐
            │ 1:N
            ├──→ knowledge_nodes ──┐
            │         │            │ 1:N
            │         │ 1:N        ├──→ questions ──→ answers
            │         │            │      │              │
            │         ▼            │      │              ▼
            └──→ resource_chunks   │      ▼         node_mastery
                 (+ pgvector)      │  question_stats
                                   │
                              exams ┘
```

| 表 | 記錄數量級 | 說明 |
|----|-----------|------|
| resources | 每人 5-50 | 上傳的文件 |
| knowledge_nodes | 每資源 5-50 | 章節結構 |
| resource_chunks | 每資源 20-200 | 語意切塊 + 向量 |
| questions | 每考試 10-100 | 考題（考古+AI） |
| answers | 每考試 10-100 | 作答記錄 |
| node_mastery | 每人每節點 1 | 掌握度追蹤 |
| question_stats | 每人每節點 1 | SM-2 記憶追蹤 |

---

## 支援的檔案類型

| 類型 | 副檔名 | 處理方式 | 最終產物 |
|------|--------|---------|---------|
| PDF | .pdf | PyMuPDF + AI 結構分析 | 章節樹 + 向量 chunks |
| Markdown | .md | 標題語法切分 | 節點 + chunks |
| 純文字 | .txt | 段落切分 | 節點 + chunks |
| 手寫圖片 | .jpg/.png | Claude Vision OCR | 單節點 + chunks |
| YouTube | URL | 字幕/摘要提取 | 節點 + chunks |

---

## 關鍵設定

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `CHUNK_SIZE_TOKENS` | 512 | 每個 chunk 的 token 數 |
| `CHUNK_OVERLAP_TOKENS` | 128 | chunk 間重疊 token 數 |
| `HISTORICAL_RATIO` | 0.20 | 考古題佔比 20% |
| Embedding model | Voyage AI | 1024 維向量 |
| LLM | Claude (Anthropic) | 結構分析 + 出題 |
