# TiTi Commander — CertiMate 開發工作原則

**版本：** v1.0  
**最後更新：** 2026-04-10  
**開發哲學：** Vibe Coding + 智慧結構化

---

## 🎯 核心原則

我們採用 **Vibe Coding** 開發模式，但加入**最少必要的結構**來確保代碼質量和可維護性。

### 1️⃣ 保持開發速度（Vibe Coding）

**原則：**
- 快速迭代、快速反饋
- 功能優先、完美次之
- 實驗和學習驅動開發
- 不被過度工程化所困

**實踐：**
```bash
# 快速開發循環（目標 <2 秒）
cd backend && .venv/bin/python -m uvicorn app.main:app --reload
cd frontend && npm run dev

# 快速測試反饋
.venv/bin/python -m behave tests/features/FEATURE_NAME.feature --no-capture
```

---

### 2️⃣ 智慧結構化（不過度設計）

**原則：**
- 足夠的結構來避免混亂
- 不強制完美
- 根據需要漸進式改進
- 技術債務視為機會，不是包袱

**實踐：**
```
├─ 代碼組織：分層架構（Router → Service → Repository）
├─ 類型安全：Python 3.11 類型提示（漸進式）
├─ 測試：BDD 優先（已有 43 個 feature）
└─ 重構：定期優化，不打破功能
```

---

## 📐 技術堆棧

| 層級 | 技術 | 理由 |
|------|------|------|
| **前端** | Next.js 15 + React 19 + TypeScript | 快速、全類型化 |
| **後端** | FastAPI + Python 3.11 | 快速迭代、自動文檔 |
| **數據庫** | PostgreSQL 15 + pgvector | 可靠、支援 AI embedding |
| **ORM** | SQLAlchemy 2.0 | 靈活、自動遷移 |
| **測試** | Behave BDD | 業務需求→自動化測試 |
| **部署** | GCP (Cloud Run + Firebase) | 自動擴展、低成本 |

---

## 🛠️ 四大改進實踐

### 1. 📝 添加更多類型提示（Python 3.11）

**目標：** 逐步提高類型安全，但不強制 100%

**後端實踐：**

```python
# ❌ 舊（無類型提示）
def get_map(subject_id):
    return service.fetch_knowledge_map(subject_id)

# ✅ 新（有類型提示）
from typing import Optional
from uuid import UUID

def get_map(subject_id: UUID) -> dict[str, Any]:
    """取得知識圖譜數據。
    
    Args:
        subject_id: 學科 ID
        
    Returns:
        知識圖譜結構化數據
    """
    return service.fetch_knowledge_map(subject_id)
```

**實施策略：**
- ✅ 新文件全部加類型提示
- ✅ 修改現有文件時順便改
- ✅ 不強制重構老代碼（技術債，待定）
- ✅ 使用 `|` 聯合類型（Python 3.10+）

**驗證工具：**
```bash
# 檢查類型（可選）
python -m mypy backend/app --ignore-missing-imports --no-error-summary
```

---

### 2. 🏗️ 改進 Service 層的一致性

**目標：** Service 層是業務邏輯的唯一入口

**當前問題：**
```
❌ 33 個 Service 直接 query DB（繞過 Repository）
❌ 4 個混用 Repository + 直接查詢
❌ 錯誤處理不一致
```

**標準模式：**

```python
# backend/app/services/base.py
from typing import Any

class BaseService:
    """所有 Service 的基類。"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def ok(self, data: Any = None, **kwargs) -> dict:
        """標準成功回應。"""
        return {"error": False, "data": data, **kwargs}
    
    def error(self, message: str, status_code: int = 400, **kwargs) -> dict:
        """標準錯誤回應。"""
        return {"error": True, "message": message, "status_code": status_code, **kwargs}

# backend/app/services/knowledge_map_service.py
class KnowledgeMapService(BaseService):
    """知識圖譜服務。"""
    
    def get_map(self, subject_id: str, user_id: str) -> dict:
        """取得知識圖譜。
        
        Returns:
            {"error": False, "data": {...}} 或 {"error": True, "message": "..."}
        """
        try:
            # 優先使用 Repository
            map_data = self.knowledge_repo.get_by_subject(subject_id)
            
            # 如無對應 Repository，用 BaseService helper
            if not map_data:
                nodes = self.db.query(KnowledgeNode).filter(
                    KnowledgeNode.subject_id == subject_id
                ).all()
                map_data = {"nodes": nodes}
            
            return self.ok(map_data)
        except Exception as e:
            return self.error(f"取得知識圖譜失敗: {str(e)}", 500)
```

**逐步改進計畫：**
- ✅ 新 Service 必須繼承 BaseService
- ✅ 優先使用 Repository；若無則使用 `self.db.query()`（暫時）
- 🟡 定期重構老 Service（低優先級）
- 🟡 為常用查詢建立 Repository（漸進）

**驗證方式：**
```bash
# 檢查 Service 層模式
grep -r "class.*Service" backend/app/services/*.py | head -10
```

---

### 3. 🧪 完善 BDD 測試（已有 43 個）

**目標：** 測試驅動開發，但保持靈活

**當前狀態：**
```
✅ 43 個 .feature 文件
✅ 250+ 個 step definitions
✅ 完整的 E2E 測試覆蓋
🟡 部分 feature 標記為 @ignore（未完成）
```

**實踐：**

```bash
# 執行所有測試（排除未完成）
.venv/bin/python -m behave tests/features/ --tags=~@ignore

# 執行特定 feature
.venv/bin/python -m behave tests/features/03-知識心智圖.feature --no-capture

# 執行特定標籤
.venv/bin/python -m behave tests/features/ --tags=@knowledge_map
```

**新功能開發流程：**

```
1. 寫 .feature 文件（Gherkin）描述需求
   Feature: 動態知識圖譜導航
     Scenario: 點擊節點展開詳情
       Given 使用者有知識圖譜
       When 使用者點擊知識節點
       Then 顯示節點詳情

2. 標記為 @ignore（暫時跳過）
   @ignore
   Scenario: ...

3. 實作 Step Definitions
   @when("使用者點擊知識節點")
   def step_user_clicks_node(context):
       # 實作...

4. 移除 @ignore，測試通過
   .venv/bin/python -m behave tests/features/XX.feature

5. 部署前驗證
   .venv/bin/python -m behave tests/features/ --tags=~@ignore
```

**不強制 100% 測試覆蓋：**
- ✅ 功能路徑必須測試（BDD）
- 🟡 邊界情況（可選，優先級低）
- 🟡 工具函數（單元測試，可選）

---

### 4. 🔄 定期重構（迭代改進）

**目標：** 在測試保護下改善代碼質量，小步前進

**重構週期：**
```
每 2 週一次小重構（0.5-1 天）
├─ 統一命名規範
├─ 提取重複代碼
├─ 改進函數簽名
├─ 更新類型提示
└─ 驗證：所有測試仍通過
```

**重構清單（優先序）：**

| 優先級 | 項目 | 預計時間 | 驗收標準 |
|------|------|--------|--------|
| HIGH | Service 層一致性 | 3 週 | 所有 Service 繼承 BaseService |
| HIGH | 添加類型提示 | 進行中 | 新文件 100%，舊文件 50% |
| MEDIUM | Repository 層擴展 | 4 週 | 常用查詢都有 Repository |
| MEDIUM | 錯誤處理統一 | 2 週 | 所有 API 用 `_handle_result()` |
| LOW | 代碼風格 | 1 週 | 通過 Black 格式檢查 |

**重構命令：**
```bash
# 代碼格式檢查
black backend/app --check

# 類型檢查
mypy backend/app --ignore-missing-imports

# 執行測試（確保沒破壞）
.venv/bin/python -m behave tests/features/ --tags=~@ignore
```

---

## 📋 開發工作流

### 新功能開發流程

```
1. 分析需求
   └─ 討論設計（Slack/Email）
   └─ 不過度設計，快速開始

2. 編寫 Gherkin .feature（BDD）
   └─ 描述使用者故事
   └─ 標記 @ignore（暫時跳過）

3. 快速開發
   ├─ 後端：實作 API endpoint
   ├─ 前端：實作 UI
   └─ 每 30 分鐘測試一次

4. Step Definitions 實作
   └─ 轉換 Gherkin → Python 代碼
   └─ 所有測試通過

5. 代碼審查（簡輕）
   └─ 只檢查邏輯和類型安全
   └─ 不糾結風格

6. 合併到 main
   └─ GitHub Actions 自動部署

7. 定期重構（不阻塞功能）
   └─ 改進代碼質量
   └─ 保持測試綠燈
```

### 提交訊息規範

```
# 格式：<type>: <description>

# 示例
feat: Add dynamic knowledge graph visualization
fix: Resolve node mastery calculation bug
refactor: Improve service layer consistency
docs: Update BDD test guidelines

# 允許的 type
feat      功能新增
fix       bug 修復
refactor  代碼重構（不改功能）
perf      性能優化
test      測試相關
docs      文檔更新
chore     構建、依賴等

# 不強制，但推薦使用
```

---

## 🚀 部署工作流

### 自動部署（推薦）

```bash
# 推送到 main → GitHub Actions 自動部署
git push origin main

# Actions 自動執行：
# 1. 建置後端 Docker 映像
# 2. 推送到 Artifact Registry
# 3. 部署到 Cloud Run
# 4. 建置前端
# 5. 部署到 Firebase
# 6. 執行 Smoke Test
```

### 手動部署（緊急用）

```bash
cd /home/user/certimate
./deploy.sh all              # 完整部署
./deploy.sh backend          # 只後端
./deploy.sh frontend         # 只前端
```

---

## 📊 質量指標

我們追蹤（但不強制）以下指標：

| 指標 | 目標 | 工具 |
|------|------|------|
| **BDD 測試通過率** | ≥ 90% | Behave |
| **類型提示覆蓋** | ≥ 60% | mypy |
| **Service 層一致性** | 100% | Code Review |
| **部署成功率** | = 100% | GitHub Actions |
| **生產環境 bug** | 儘可能少 | Cloud Run Logs |

---

## 💡 禁止事項（保護 Vibe Coding）

❌ **不要：**
- 過度設計（YAGNI 原則）
- 完美主義（功能優先）
- 一次性改重所有舊代碼
- 強制 100% 類型提示或測試覆蓋
- 長時間討論而不編碼
- 為假想的未來需求預留設計

✅ **要做：**
- 快速實驗和迭代
- 漸進式改進
- 優先發佈功能
- 根據實際性能瓶頸優化
- 小步提交，頻繁反饋
- 定期重構小部分代碼

---

## 🎯 短期目標（4 週）

- [ ] 完成 GCP 部署（GitHub Actions）
- [ ] 新知識圖譜上線驗證
- [ ] 後端 30% 文件添加類型提示
- [ ] Service 層 5 個主要 Service 重構為 BaseService
- [ ] 添加 2-3 個新 feature（完整 BDD）

## 🎯 中期目標（3 個月）

- [ ] 後端 70% 文件有類型提示
- [ ] 所有新 Service 繼承 BaseService
- [ ] 常用查詢都有 Repository
- [ ] 前端類型覆蓋 100%
- [ ] 43 個 feature 的 100% 通過率（移除 @ignore）

## 🎯 長期目標（1 年）

- [ ] 後端 90%+ 類型提示覆蓋
- [ ] Service 層完全統一
- [ ] 考慮性能瓶頸，評估 Rust 微服務可行性
- [ ] 完整的文檔和開發指南
- [ ] 可交接給新團隊成員

---

## 📞 聯繫和反饋

- 有改進建議？提交 PR 到 TITI_COMMANDER.md
- 遇到阻礙？Slack 討論，不要獨自悶著
- 覺得某個實踐不合適？提議修改

---

**最後的話：**

> TiTi Commander 不是一套死板的規則，而是**智慧的指引**。  
> 保持 Vibe Coding 的自由和靈活，同時添加足夠的結構來避免混亂。  
> 代碼會改變，但原則保持不變：**快速迭代，小步改進，保持簡單。**

---

**版本紀錄：**
- v1.0 (2026-04-10): 初始版本，包含 4 大改進實踐
