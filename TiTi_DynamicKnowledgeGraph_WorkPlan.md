# TiTi 動態知識庫與雙向連結 — 工作排程

**建立日期**：2026-04-09
**技術規格**：`project/03_research_and_development/動態知識庫與雙向連結 技術實作指引.md`
**董事會決策**：啟動 / 不用 feature flag / 含歷史 SM-2 重播 / Celery+Redis 本地建立

---

## 架構變更摘要

| 維度 | 現狀 | 新架構 |
|------|------|--------|
| 進度儲存 | 靜態 progress_percentage | `base_mastery` + `ease_factor` + 時間錨點 |
| 衰退機制 | 無 | 指數衰退（read-time 計算） |
| 考試處理 | 同步 | 非同步（Redis 佇列 + Celery Worker） |
| 練習影響 | 寫入 state machine | 不影響 DB（僅本地回饋） |
| 父節點聚合 | DB 計算 | 客戶端 Web Worker |
| 考綱版本 | 版本切換 | 軟合併 + 動態重算 |

---

## Phase 1：Schema & Migration（預估 3 天）

### P1.1 更新 Feature 03 規格 🔒 GF Gate

**角色**：產品經理
**OKR**：O3-KR3（弱點考點重複練習後答對率提升 ≥ 15%）

新增 Scenario 到 Feature 03/03b：

```gherkin
# 03-知識心智圖.feature 新增
Rule: 後置（狀態）- 節點進度應隨時間自然衰退，反映記憶遺忘曲線

  Example: 超過複習期限的節點顯示衰退後的有效進度
    Given 使用者 "pro@example.com" 的節點 "EC2 運算服務" 基礎掌握度為 0.85
    And 該節點的下次複習日期為 7 天前
    When 使用者查看知識心智圖
    Then 節點 "EC2 運算服務" 的有效進度應低於 85%
    And 節點顏色應從綠色漸變為黃色

  Example: 未超過複習期限的節點維持原始進度
    Given 使用者 "pro@example.com" 的節點 "S3 儲存" 基礎掌握度為 0.90
    And 該節點的下次複習日期為 3 天後
    When 使用者查看知識心智圖
    Then 節點 "S3 儲存" 的有效進度應為 90%

Rule: 命令（喚醒）- 衰退節點可透過 Refresh Quiz 恢復

  Example: 完成 Refresh Quiz 後節點進度恢復
    Given 使用者 "pro@example.com" 有一個已衰退的節點 "IAM 身分管理"
    When 使用者點擊「記憶喚醒」並完成迷你測驗全部答對
    Then 節點 "IAM 身分管理" 的下次複習日期應延長至 14 天後
    And 有效進度應恢復至基礎掌握度

Rule: 後置（隔離）- 練習模式不影響知識圖譜狀態

  Example: 練習模式答題不更新掌握度
    When 使用者在練習模式回答題目並答對
    Then 知識圖譜的節點掌握度不應改變
    And 使用者應看到正確答案與詳解

Rule: 後置（結算）- 考試交卷後觸發全螢幕結算動畫

  Example: 考試結算後顯示成長敘事動畫
    When 使用者 "pro@example.com" 完成正式考試並交卷
    Then 系統應顯示全螢幕結算動畫
    And 動畫應包含「升級考點數、發現盲點數、整體進度變化」
```

### P1.2 新增 syllabus_topics 表

**角色**：後端研發
**依賴**：P1.1 批准

```sql
-- DBML 新增
Table syllabus_topics {
  id uuid [pk, default: `gen_random_uuid()`]
  parent_id uuid [ref: > syllabus_topics.id]
  name varchar(255) [not null]
  depth int [not null]
  weight float [default: 1.0]
  prerequisite_topic_id uuid [ref: > syllabus_topics.id, note: '前置知識溯源']
  is_active boolean [default: true, note: '軟刪除']
  merged_into_id uuid [ref: > syllabus_topics.id, note: '合併繼承']
  created_at timestamptz [default: `now()`]
  updated_at timestamptz [default: `now()`]
}
```

### P1.3 重構 user_topic_states

**角色**：後端研發
**依賴**：P1.2

```sql
-- 新增欄位（保留舊欄位 2 週後移除）
ALTER TABLE node_mastery ADD COLUMN base_mastery FLOAT DEFAULT 0.0;
ALTER TABLE node_mastery ADD COLUMN ease_factor FLOAT DEFAULT 2.5;
ALTER TABLE node_mastery ADD COLUMN last_tested_at TIMESTAMPTZ;
ALTER TABLE node_mastery ADD COLUMN next_review_at TIMESTAMPTZ;
ALTER TABLE node_mastery ADD COLUMN status VARCHAR(20) DEFAULT 'UNSEEN';
-- status: UNSEEN / CRITICAL / PENDING / MASTERED
```

### P1.4 Alembic Migration 041

**角色**：後端研發
**依賴**：P1.3

檔案：`alembic/versions/041_add_syllabus_topics_and_decay.py`

### P1.5 資料回填

**角色**：後端研發
**依賴**：P1.4

```sql
-- 回填 node_mastery 舊資料
UPDATE node_mastery SET
  base_mastery = COALESCE(mastery_rate, 0.0),
  last_tested_at = updated_at,
  next_review_at = updated_at + interval '14 days',
  status = CASE
    WHEN mastery_rate >= 0.7 THEN 'MASTERED'
    WHEN mastery_rate >= 0.4 THEN 'PENDING'
    WHEN mastery_rate > 0 THEN 'CRITICAL'
    ELSE 'UNSEEN'
  END
WHERE base_mastery = 0.0 OR base_mastery IS NULL;
```

---

## Phase 2：後端 API 改造（預估 4 天）

### P2.1 SM-2 State Machine 核心

**角色**：後端研發
**OKR**：O1-KR1

新增：`app/services/sm2_engine.py`

```python
class SM2Engine:
    """SuperMemo 2 狀態機 — 考試結果驅動掌握度更新。"""
    
    def process_answer(self, state: UserTopicState, is_correct: bool, quality: int) -> UserTopicState:
        """處理單題答案，更新 ease_factor + base_mastery + next_review_at"""
    
    def calculate_retention(self, state: UserTopicState, now: datetime) -> float:
        """Read-time 計算有效記憶保留率"""
        # Retention = 1.0 if now <= next_review_at
        # Retention = max(0.7, e^(-λ(now - next_review_at))) if decayed
    
    def calculate_effective_progress(self, state: UserTopicState, now: datetime) -> float:
        """有效進度 = base_mastery × retention"""
```

### P2.2 Async Exam Submit (Celery + Redis)

**角色**：後端研發 + 運營工程師
**依賴**：P2.1

```bash
# 本地 Redis
docker run -d --name certimate-redis -p 6379:6379 redis:7-alpine

# Celery Worker
.venv/bin/celery -A app.worker worker --loglevel=info
```

新增：
- `app/worker.py` — Celery app 初始化
- `app/tasks/exam_settlement.py` — 考試結算任務
- `POST /exams/{id}/submit` 改為回傳 `202 Accepted`，交由 worker 處理

### P2.3 Draft Checkpoint (Redis)

**角色**：後端研發
**依賴**：P2.2

- `PATCH /exams/{id}/draft` — 每 30 秒存 Redis，不觸發 state machine
- Key: `exam_draft:{exam_id}` TTL: 24 小時

### P2.4 Refresh Quiz API

**角色**：後端研發
**依賴**：P2.1

- `POST /topics/{topic_id}/refresh-quiz` — 生成 1-3 題迷你測驗
- 全部答對 → `next_review_at` 延長 14 天，effective progress 恢復

### P2.5 Practice vs Exam 隔離

**角色**：後端研發
**依賴**：P2.1

- `POST /practice/submit` — 回傳正確答案 + 詳解，**不寫 DB**
- 前端練習模式呼叫此端點，而非 `/exams/{id}/submit`

### P2.6 Read-time Decay 加入 API

**角色**：後端研發
**依賴**：P2.1

修改 `GET /knowledge-map/subjects/{id}/nodes`：
- 回傳每個節點的 `effective_progress`（base_mastery × retention）
- 回傳 `decay_status`: `fresh` / `decaying` / `critical`
- 回傳 `next_review_at` 供前端顯示

---

## Phase 3：前端改造（預估 4 天）

### P3.1 Web Worker 客戶端聚合

**角色**：前端研發
**依賴**：P2.6

新增：`frontend/workers/progress-aggregator.ts`

```typescript
// Web Worker: 遞迴聚合 parent progress
// Input: flat array of { nodeId, parentId, effectiveProgress, weight }
// Output: { nodeId, aggregatedProgress }[]
```

### P3.2 知識圖譜 UI 改造

**角色**：前端研發
**依賴**：P3.1

- 節點顏色：綠（fresh）→ 黃閃爍（decaying）→ 紅（critical）
- Tooltip：「🕒 記憶已衰退，建議刷新複習」
- MindMapTree component 改用 effective_progress

### P3.3 考試結算動畫

**角色**：前端研發
**依賴**：P2.2

新增：`components/ExamSettlementScreen.tsx`

- WebSocket 監聽 `EXAM_SETTLED` 事件
- 全螢幕動畫：升級考點數 → 盲點偵測 → 整體進度變化

### P3.4 Refresh Quiz Modal

**角色**：前端研發
**依賴**：P2.4

新增：`components/RefreshQuizModal.tsx`

- 一鍵「喚醒記憶」按鈕
- 1-3 題迷你測驗
- 全對 → 進度恢復動畫

### P3.5 儀表板 Decay 顯示

**角色**：前端研發
**依賴**：P3.1

- Dashboard 進度指標改用 effective_progress
- 新增「需要複習」計數器

### P3.6 Topology Change Toast

**角色**：前端研發
**依賴**：P1.2

- 考綱擴展時 Toast：「🎉 知識庫擴展！當前掌握度已調整為 {percent}%」

---

## Phase 4：測試 & 驗收（預估 2 天）

### P4.1 BDD Feature 03 紅綠燈

**角色**：測試工程師
**依賴**：P3.2

- 新增 decay scenario step definitions
- 驗證 effective_progress 計算正確

### P4.2 SM-2 單元測試

**角色**：測試工程師
**依賴**：P2.1

- 驗證 ease_factor 更新公式
- 驗證 retention 衰退曲線
- 邊界測試：ease_factor 最小值、最大衰退

### P4.3 Practice/Exam 隔離 E2E

**角色**：測試工程師
**依賴**：P2.5

- 驗證練習不影響 node_mastery
- 驗證考試正確更新 base_mastery

---

## Phase 5：遷移 & 上線（預估 1 天）

### P5.1 Production Migration

**角色**：運營工程師
**依賴**：P4.x 全通過

### P5.2 歷史考試 SM-2 重播

**角色**：後端研發
**依賴**：P5.1

新增：`app/scripts/replay_exam_history.py`
- 依時間順序重播所有歷史考試記錄
- 用 SM-2 引擎重建真實 base_mastery 和 ease_factor

---

## 基礎設施需求

### Redis（本地開發）
```bash
docker run -d --name certimate-redis -p 6379:6379 redis:7-alpine
```

### Celery Worker
```bash
# 新增 .env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# 啟動
.venv/bin/celery -A app.worker worker --loglevel=info
```

### Docker Compose 更新
```yaml
services:
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

---

## 檔案異動清單

### 新增檔案
| 檔案 | 說明 |
|------|------|
| `app/services/sm2_engine.py` | SM-2 狀態機核心 |
| `app/worker.py` | Celery app |
| `app/tasks/exam_settlement.py` | 考試結算任務 |
| `app/models/syllabus_topic.py` | 考綱骨架 ORM |
| `app/api/practice.py` | 練習模式 API |
| `app/api/refresh_quiz.py` | 記憶喚醒 API |
| `app/scripts/replay_exam_history.py` | SM-2 歷史重播 |
| `alembic/versions/041_*.py` | Schema migration |
| `frontend/workers/progress-aggregator.ts` | Web Worker |
| `frontend/components/ExamSettlementScreen.tsx` | 結算動畫 |
| `frontend/components/RefreshQuizModal.tsx` | 記憶喚醒 |

### 修改檔案
| 檔案 | 改動 |
|------|------|
| `app/models/node_mastery.py` | 新增 base_mastery/ease_factor/timestamps |
| `app/api/exam.py` | submit 改 async |
| `app/api/knowledge_map.py` | 回傳 effective_progress |
| `app/services/mock_exam_service.py` | 調用 SM-2 引擎 |
| `app/services/knowledge_nav_service.py` | decay 計算 |
| `frontend/app/knowledge/page.tsx` | 使用 Web Worker |
| `frontend/app/exam/workspace/page.tsx` | draft checkpoint |
| `frontend/app/dashboard/page.tsx` | decay 顯示 |
| `frontend/components/MindMapTree.tsx` | decay 顏色 |
| `project/specs/entity/erm.dbml` | 新增 syllabus_topics |
| `tests/features/03-*.feature` | 新增 decay scenario |

---

## 執行順序（批次化）

```
Session 1（P1 全部）: Schema + Migration + 資料回填
Session 2（P2.1-2.2）: SM-2 引擎 + Celery/Redis
Session 3（P2.3-2.6）: Draft + Refresh + Practice + Decay API
Session 4（P3.1-3.2）: Web Worker + 知識圖譜 UI
Session 5（P3.3-3.6）: 結算動畫 + Modal + 儀表板 + Toast
Session 6（P4 + P5）: 測試 + 遷移 + SM-2 重播
```

---

*文件位置*：`project/TiTi_DynamicKnowledgeGraph_WorkPlan.md`
*維護者*：CEO 總指揮
*狀態*：🔒 G1 已批准，Phase 1 開始
