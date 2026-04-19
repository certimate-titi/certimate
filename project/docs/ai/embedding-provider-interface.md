# Embedding Provider 抽象介面設計

**文件編號**: AI-embedding-provider-interface
**產出角色**: AI/ML 工程師 + 資料庫工程師（CTO 技術線）
**產出日期**: 2026-04-14
**狀態**: Draft v1
**對應 Feature**: 33 — 成本監控中心
**依據決策**: 採納策略 D + 預留未來雙軌向量庫空間

---

## 1. 目的

Feature 33 本次**不實作** provider 切換，但必須在架構層預留「未來可無痛遷移至多 provider 並存」的介面。本文件定義預留機制與未來遷移路徑，供後端工程師在 Layer 3 實作時參考。

## 2. 預留機制（本次已納入）

### 2.1 Schema 層預留（migration 049 已完成）

```sql
ALTER TABLE resource_chunks
    ADD COLUMN embedding_provider varchar(32) NOT NULL DEFAULT 'voyage',
    ADD COLUMN embedding_model    varchar(64) NOT NULL DEFAULT 'voyage-3';

CREATE INDEX idx_resource_chunks_embedding_provider
    ON resource_chunks(embedding_provider);
```

**設計理由**：
- 新資料寫入時必須記錄 provider，避免未來混用時無從追溯
- 既有資料 default 為 `voyage` / `voyage-3`，不需 backfill
- 加索引使「依 provider 分流查詢」成本低

### 2.2 Status Enum 預留

```sql
ALTER TYPE resource_status ADD VALUE 'PENDING_BUDGET_RECOVERY';
```

用於降級佇列語意表達，避免與既有 `PENDING` / `FAILED` 混淆。

## 3. 應用層抽象介面（Layer 3 後端工程師必須實作）

### 3.1 介面定義

```python
# backend/app/services/embedding/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Sequence


@dataclass(frozen=True)
class EmbeddingResult:
    vector: List[float]
    provider: str          # "voyage" / "gemini" / "openai"
    model: str             # e.g. "voyage-3", "text-embedding-004"
    dimension: int
    input_tokens: int
    cost_usd: float


@dataclass(frozen=True)
class EmbeddingRequest:
    text: str
    task_type: str         # "document" / "query"
    feature: str           # "mindmap" / "retrieval" / "rag"


class EmbeddingProvider(ABC):
    """All embedding providers must implement this interface."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @property
    @abstractmethod
    def dimension(self) -> int: ...

    @abstractmethod
    def embed_one(self, req: EmbeddingRequest) -> EmbeddingResult: ...

    @abstractmethod
    def embed_batch(self, reqs: Sequence[EmbeddingRequest]) -> List[EmbeddingResult]: ...

    @abstractmethod
    def estimate_cost(self, text: str) -> float:
        """Return estimated USD cost before actual API call."""
```

### 3.2 Provider 實作

本次只實作 `VoyageProvider`，未來可擴充：

```python
# backend/app/services/embedding/voyage_provider.py
class VoyageProvider(EmbeddingProvider):
    provider_name = "voyage"
    model_name = "voyage-3"
    dimension = 1024
    # ... 呼叫 Voyage API，回傳 EmbeddingResult

# 未來新增時：
# backend/app/services/embedding/gemini_provider.py
# backend/app/services/embedding/openai_provider.py
```

### 3.3 Provider Registry + Selector

```python
# backend/app/services/embedding/registry.py

_PROVIDERS: dict[str, EmbeddingProvider] = {}

def register(provider: EmbeddingProvider) -> None:
    _PROVIDERS[provider.provider_name] = provider

def get(name: str) -> EmbeddingProvider:
    return _PROVIDERS[name]

def get_default() -> EmbeddingProvider:
    """根據設定檔選擇預設 provider，預設 voyage。"""
    return _PROVIDERS[settings.DEFAULT_EMBEDDING_PROVIDER]
```

### 3.4 呼叫端永遠透過 Registry

```python
# ❌ 不要直接呼叫 Voyage API
voyage.embed(text)

# ✅ 透過 registry + quota service
quota_service.check_and_reserve(cost)
provider = embedding_registry.get_default()
result = provider.embed_one(EmbeddingRequest(text=text, task_type="document", feature="mindmap"))
chunk.embedding = result.vector
chunk.embedding_provider = result.provider  # 必須寫入
chunk.embedding_model = result.model        # 必須寫入
ledger.record(result)
```

### 3.5 查詢端依 provider 分流（未來啟用時）

```python
# backend/app/services/embedding/retrieval.py

def similarity_search(query: str, resource_id: UUID) -> List[ResourceChunk]:
    # 1. 查該資源的 chunks 用哪個 provider embed
    provider_name = db.query(ResourceChunk.embedding_provider)\
        .filter_by(resource_id=resource_id)\
        .first()[0]

    # 2. 用同一 provider embed query
    provider = embedding_registry.get(provider_name)
    query_vec = provider.embed_one(EmbeddingRequest(text=query, task_type="query", feature="retrieval"))

    # 3. 只在同 provider 的 chunks 裡做向量搜尋
    return db.query(ResourceChunk)\
        .filter(ResourceChunk.resource_id == resource_id)\
        .filter(ResourceChunk.embedding_provider == provider_name)\
        .order_by(ResourceChunk.embedding.cosine_distance(query_vec.vector))\
        .limit(10).all()
```

**關鍵**：查詢時必須用**寫入時的同一 provider** 做 query embedding，絕對不可跨 provider 混用。

## 4. 未來遷移路徑（不在本次實作範圍）

### Phase X — 當真的需要雙軌向量庫時

1. **新增 Gemini provider**：實作 `GeminiProvider(EmbeddingProvider)`
2. **Schema 擴充**：
   ```sql
   ALTER TABLE resource_chunks
       ADD COLUMN embedding_768 vector(768);
   CREATE INDEX ... USING hnsw (embedding_768 vector_cosine_ops);
   ```
3. **寫入邏輯**：`embedding` 或 `embedding_768` 擇一寫入，依 provider.dimension 決定
4. **查詢邏輯**：依 `embedding_provider` 分流到不同欄位與索引
5. **切換策略**：
   - 新資源走 Gemini（成本較低、Google 基礎設施穩定）
   - 既有 Voyage 資源保留不動，繼續查詢
   - 當 Voyage 向量庫規模降至可接受時，背景批次重嵌到 Gemini
6. **Feature Flag**：`DEFAULT_EMBEDDING_PROVIDER` 設定檔切換，不需改程式

### 遷移觸發條件（建議閾值）

- Voyage 月成本連續 3 個月超過 $200（遠高於本次預算 $50）
- 或 Voyage API 穩定性下降（單月失敗率 > 1%）
- 或商業策略變動（例如與 Google Cloud 深度合作取得優惠）

## 5. 本次 Layer 3 必須遵守的規範

後端工程師在實作 `cost_monitor` router 與 embedding 改造時：

- [ ] 必須把 Voyage 呼叫包裝在 `VoyageProvider` 類別內，不可散落各處直接 `import voyageai`
- [ ] 所有 embedding 呼叫必須經過 `embedding_registry.get_default()`
- [ ] 寫入 `resource_chunks` 時必須同步寫入 `embedding_provider` + `embedding_model`
- [ ] 查詢時必須先讀 `embedding_provider` 欄位（即使目前永遠是 `voyage`）
- [ ] `voyage_quota_service.check_and_reserve()` 必須在 `provider.embed_one()` 之前呼叫
- [ ] 失敗時依 Feature File Scenario：達 80% 時新資源設為 `PENDING_BUDGET_RECOVERY`，達 100% 時硬性拒絕

## 6. 給 CTO 的三句話

1. 本次預留了 **schema 欄位 + 應用層 Interface** 兩層介面，未來切換 provider 時**不需動資料庫結構，只需新增 provider class**
2. **查詢永遠用寫入時的同 provider**，這是向量檢索正確性的鐵律
3. 雙軌向量庫（策略 C）不在本次範圍，但 Layer 3 實作必須遵守本文件第 5 節規範，否則未來遷移會變成大工程
