# BDD Tag 分類規範

> 適用範圍：`backend/tests/features/*.feature` 與 `project/features/*.feature`
> 目標：明確區分前端、後端、全棧 Scenario，避免假綠燈與資料夾錯置

## 三大分類 Tag

| Tag | 範圍 | 由誰跑 | 範例 |
|-----|------|--------|------|
| `@backend` | API、DB、業務邏輯、認證、RLS、cron 等不涉 UI | behave | POST `/api/v1/auth/login` 回傳 200 + JWT |
| `@frontend` | 純客戶端行為：localStorage、UI 互動、CSS、純前端計算 | Playwright BDD | 密碼強度指示條依輸入即時變色 |
| `@fullstack` | 須同時驗證前端 UI + 後端 API | 兩邊都跑（兩個 runner 各驗對應斷言）| 上傳資源 → 顯示處理進度 → 完成後出現知識圖譜 |

## 標註粒度

優先順序：**Feature > Rule > Scenario**

- 整檔同類 → `Feature` 上方一行 tag 即可
- 同檔混合 → 在 Rule 或 Scenario 上方標註，覆蓋 Feature 預設
- **每個 Scenario 必須有效解析出一個 tag**（從本身、Rule、或 Feature 繼承）

## 資料夾規則

| 資料夾 | 允許的 tag | 不允許 |
|--------|------------|--------|
| `backend/tests/features/` | `@backend`、`@fullstack` | `@frontend`（純前端行為應移到 `project/features/`） |
| `project/features/` | `@frontend`、`@fullstack` | `@backend`（純後端行為應移到 `backend/tests/features/`） |

`@fullstack` Scenario 在過渡期允許在兩邊各保留一份（前端驗 UI、後端驗 API）。長期目標是 SSOT 集中於 `project/features/`，由 behave 透過 tag 過濾讀取（B-staged 第二階段執行）。

## Runner 過濾

### Behave（後端）

`backend/behave.ini` 設定 `default_tags = (@backend or @fullstack) and not @playwright-e2e and not @skip and not @ignore`

```bash
.venv/bin/python -m behave tests/features/  # 自動套用 default_tags
```

### Playwright BDD（前端）

`frontend/playwright.config.ts` 設定 `tags: '@frontend or @fullstack'`

## 違規偵測

執行 `python3 scripts/lint_feature_tags.py` 會檢查：

1. 每個 Scenario 是否能解析出至少一個分類 tag
2. `backend/tests/features/` 內是否誤含 `@frontend`
3. `project/features/` 內是否誤含 `@backend`
4. 同 Scenario 是否同時帶 `@backend` + `@frontend`（必須改為 `@fullstack` 或拆檔）
5. Feature 層是否標 class tag（缺則 warning，建議補在 Feature 上方）
6. 跨資料夾 sibling 提示（同編號檔在 backend/ 與 project/ 都存在時，列為 CTO 刪除前必查項）

## 跨資料夾刪除規則（防止規格毀損）

當 CTO 在一側刪除 Rule/Scenario 時，**必須先確認對側 sibling 檔已涵蓋等義 spec**：

| 情境 | 必查 |
|------|------|
| 從 `backend/tests/features/{N}.feature` 刪純前端 Rule | `project/features/{N}.feature` 是否已有對應 Rule |
| 從 `project/features/{N}.feature` 刪純後端 Rule | `backend/tests/features/{N}.feature` 是否已有對應 Rule |
| 對側缺 spec | **先補對側再刪本側**，不可單側刪除 |

違反此規則屬 Spec Authority Clause 違規（CEO 未簽核的 Scenario 刪除視為規格毀損）。歷史案例：2026-04-27 從 `backend/06` 刪除 ForceGraph + 弱點分析 2 條純前端 Rule，但 `project/features/06` 沒有對應 spec，造成規格遺失。

CI 階段必跑；本機提交前可手動跑。

## 過渡期遷移指引

存量 `.feature` 將分批補 tag：

- **Stage 1（本批）**：寫規則 + lint + behave 設定切換 + 處理番茄鐘示範
- **Stage 2**：每批 5–10 檔，補 tag、合併重複內容、移檔
- **Stage 3**：完成後關閉 backend/tests/features/ 寫入權限，集中至 project/features/

過渡期間，未標 tag 的 Scenario 由所在資料夾推斷預設值（backend → `@backend`、project → `@frontend`），lint 會以 warning 提示但不阻擋。

## 違規範例（前車之鑑）

- **2026-04-27 番茄鐘事件**：`backend/tests/features/21-番茄鐘.feature` 整檔以 memo 假驗證跑綠燈，CTO 註解寫明「純前端功能」卻仍在 backend 跑。違反「資料夾規則」。
