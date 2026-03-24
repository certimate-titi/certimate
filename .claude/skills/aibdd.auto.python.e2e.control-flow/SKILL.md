---
name: aibdd.auto.python.e2e.control-flow
description: Python E2E 全自動批次迴圈。掃描 features 目錄，為每個 .feature 展開完整的 5 phase TODO 清單（schema-analysis → step-template → red → green → refactor），然後逐一執行直到全數完成。
user-invocable: true
argument-hint: "[features-dir]"
input: features 目錄路徑（含所有 .feature 檔案）
output: 每個 feature 完成完整 TDD 循環
---

# 指令

你是全自動 BDD 批次執行器。你的工作是：
1. 掃描 feature 檔案
2. 用 TodoWrite 建立完整的任務清單
3. 逐一執行每個任務直到全部完成
4. 不要停下來、不要問問題、不要等待指示

---

# Step 1：掃描 Feature 檔案

讀取以下目錄，找出所有 `.feature` 檔案：

```
${FEATURES_DIR}
```

按檔名排序，記錄完整路徑。

---

# Step 2：用 TodoWrite 建立任務清單

對每個 feature 檔案，建立 5 個 TodoWrite 任務。

格式規則：
- `content`：`{feature 檔名} — {phase 名稱}`
- `activeForm`：`{phase 動詞}：{feature 檔名}`
- `status`：全部設為 `pending`

範例（假設有 2 個 feature）：

```
content: "01-增加影片進度.feature — Schema Analysis"
activeForm: "分析 Schema：01-增加影片進度.feature"
status: pending

content: "01-增加影片進度.feature — Step Template"
activeForm: "生成 Step Template：01-增加影片進度.feature"
status: pending

content: "01-增加影片進度.feature — Red"
activeForm: "執行紅燈：01-增加影片進度.feature"
status: pending

content: "01-增加影片進度.feature — Green"
activeForm: "執行綠燈：01-增加影片進度.feature"
status: pending

content: "01-增加影片進度.feature — Refactor"
activeForm: "執行重構：01-增加影片進度.feature"
status: pending

content: "02-提交挑戰題.feature — Schema Analysis"
activeForm: "分析 Schema：02-提交挑戰題.feature"
status: pending

...以此類推
```

建完 TODO 清單後，**立即進入 Step 3 開始執行**。

---

# Step 3：逐一執行每個任務

從第一個 pending 任務開始，依序處理。每個任務的執行流程：

```
標記 TodoWrite → in_progress
        ↓
使用 Skill 工具呼叫對應的 skill（帶入 feature file 路徑作為 args）
        ↓
標記 TodoWrite → completed
        ↓
前進到下一個 pending 任務
```

## 任務與 Skill 對照表

| 任務 phase | 呼叫的 Skill |
|-----------|-------------|
| Schema Analysis | `/aibdd.auto.python.e2e.schema-analysis` |
| Step Template | `/aibdd.auto.python.e2e.step-template` |
| Red | `/aibdd.auto.python.e2e.red` |
| Green | `/aibdd.auto.python.e2e.green` |
| Refactor | `/aibdd.auto.python.e2e.refactor` |

## 呼叫方式

使用 Skill 工具，將 feature file 的完整路徑作為 `args` 傳入。

---

# Step 4：最終回歸測試

所有任務都 completed 後，執行一次完整回歸測試：

```bash
behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore
```

- 通過 → 全部完成
- 失敗 → 閱讀錯誤、修正、重新執行，直到全部通過

---

# 全自動規則

1. **不要停下來問問題**。遇到問題就自己修正。
2. **不要跳過任何任務**。每個任務都必須完成。
3. **每個 Skill 完成後立即標記 completed**，然後前進到下一個。
4. **一次只有一個任務是 in_progress**。
5. **Skill 是 lazy loading**：每次呼叫都會完整載入該 phase 的規則，不用擔心 context compaction 後遺忘。

---

# 為什麼用 TodoWrite + Skill 工具

| 機制 | 解決的問題 |
|-----|----------|
| TodoWrite | 任務進度跨 compaction 持久化，不會丟失 |
| Skill 工具 | 每次呼叫都完整載入該 phase 的指令，不受 compaction 影響 |
| 逐一執行 | 一次只處理一個任務，減少 context 壓力 |
