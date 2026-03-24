# 路徑覆蓋推導策略

## 目標

確保 Activity Diagram 中**每個節點至少被一條測試路線走過一次**。
分支點產生多條路線，每條路線走不同的分支組合。

## 演算法

### 步驟 1：建立節點序列

從 `[ACTIVITY]` 開始，依序記錄所有節點直到 `[END]`，形成一個有序的節點清單。

### 步驟 2：識別分支點

掃描節點序列，找出所有 `[DECISION]` 節點。每個 DECISION 有 N 個 BRANCH，代表 N 條可能的路徑。

### 步驟 3：展開路線

**線性區段**（無 DECISION）：
所有路線共用相同的步驟。

**單層 DECISION**（N 個 BRANCH）：
產生 N 條路線。每條路線走一個不同的 BRANCH，其餘步驟相同。

```
路線 1：前置步驟 → BRANCH:條件A → 後續步驟
路線 2：前置步驟 → BRANCH:條件B → 後續步驟
```

**串聯多層 DECISION**（DECISION A 有 M 個分支，DECISION B 有 N 個分支）：
取笛卡爾積，產生 M × N 條路線。

```
路線 1：… → BRANCH:A條件1 → … → BRANCH:B條件1 → …
路線 2：… → BRANCH:A條件1 → … → BRANCH:B條件2 → …
路線 3：… → BRANCH:A條件2 → … → BRANCH:B條件1 → …
路線 4：… → BRANCH:A條件2 → … → BRANCH:B條件2 → …
```

**嵌套 DECISION**（DECISION B 在 DECISION A 的某個 BRANCH 內）：
僅在進入該 BRANCH 的路線中展開內層 DECISION。

```
路線 1：… → BRANCH:A條件1 → BRANCH:B條件1 → …
路線 2：… → BRANCH:A條件1 → BRANCH:B條件2 → …
路線 3：… → BRANCH:A條件2 → …（不經過 DECISION B）
```

### 步驟 4：處理回流分支（Loop）

回流分支 `[BRANCH:Nx:條件 -> M]` 表示跳回步驟 M 重新執行。

處理方式：產生一條迴圈路線，展開為：
1. 走到 DECISION
2. 進入回流分支
3. 回到目標步驟再走一輪
4. 再次走到 DECISION，這次走另一條出口分支離開

迴圈最多展開**一次**（避免無限展開）。

```
迴圈路線：… → STEP:3 → DECISION:4a → BRANCH:否(→3) → STEP:3（第二輪）→ DECISION:4a → BRANCH:是 → …
```

### 步驟 5：處理 FORK 並行

`[FORK]` / `[PARALLEL]` / `[JOIN]` 表示多條路徑同時執行。

處理方式：不拆分為多條路線，而是在同一條路線中**依序驗證每條並行路徑的結果**。

```
路線步驟：… → 驗證並行路徑 A 的結果 → 驗證並行路徑 B 的結果 → …
```

## 路線數計算公式

```
總路線數 = ∏(每個獨立 DECISION 的分支數)
```

若有迴圈分支，每個迴圈額外產生一條路線。

### 範例

| Activity 結構 | 路線數 |
|--------------|--------|
| 純線性（無 DECISION） | 1 |
| 1 個 DECISION（2 分支） | 2 |
| 2 個串聯 DECISION（各 2 分支） | 2 × 2 = 4 |
| 1 個 DECISION（2 分支）+ 1 個回流分支 | 2 + 1 = 3 |
| 1 個 DECISION（3 分支）+ 1 個 FORK（2 並行） | 3（FORK 不增加路線數） |
