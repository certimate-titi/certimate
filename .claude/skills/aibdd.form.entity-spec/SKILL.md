---
name: aibdd.form.entity-spec
description: Entity 視圖的 Spec Skill。從完整的 .feature 文件推導 DBML 格式的 erm.dbml（資料模型）。每個 Feature 的 Background datatable 對應資料表，Rule 對應約束，Aggregate 共現對應關聯。可被 /discovery 調用，也可獨立使用。
user-invocable: true
args-config: arguments-template.yml
argument-hint: "[FEATURE_SPECS_DIR]"
input: ${FEATURE_SPECS_DIR}/**/*.feature (completed, no sticky notes)
output: ${ENTITY_SPECS_DIR}/erm.dbml
---

# 角色

管理 Entity 視圖。從完整的 Feature Files 機械性推導資料模型，每個 Aggregate 對應一張資料表，每條前置 Rule 對應一個約束，每個跨 Feature 的 Aggregate 共現對應一個關聯。

---

# Entry 條件

**獨立調用時**，先詢問：
- Feature Files 路徑（預設 `${FEATURE_SPECS_DIR}`）
- Entity model 輸出路徑（預設 `${ENTITY_SPECS_DIR}/erm.dbml`）

**被 `/discovery` 調用時**，由協調器提供以上資訊，不再詢問。

**前提**：所有輸入的 .feature 必須已完成（無便條紙、無 `(待澄清)` 佔位）。若發現未完成的 .feature，暫停並回報給協調器。

---

# erm.dbml 格式

使用 [DBML（Database Markup Language）](https://dbml.dbdiagram.io/docs/) 格式：

```dbml
Table <table_name> {
  id       integer    [pk, increment]
  <field>  <type>     [<constraints>]
  <field>  <type>

  Note: '<中文資料表說明>'
}

Enum <enum_name> {
  <value1>  [note: '<說明>']
  <value2>
}

Ref: <table_a>.<field> > <table_b>.<field>   // many-to-one
Ref: <table_a>.<field> - <table_b>.<field>   // one-to-one
Ref: <table_a>.<field> <> <table_b>.<field>  // many-to-many（透過 junction table）
```

---

# 從 .feature 推導資料表

## 1. 從 Background datatable 識別 Aggregate

每個 Background 的 `Given 系統中有以下<Aggregate名>：` 對應一張資料表：

```gherkin
Background:
  Given 系統中有以下商品：
    | productId | name    | price | stock |
    | 1         | MacBook | 45000 | 10    |
```
→
```dbml
Table products {
  id    integer  [pk, increment]
  name  varchar  [not null]
  price integer  [not null]
  stock integer  [not null, note: 'must be >= 0']
}
```

**規則**：
- datatable 的 key 欄位（`productId`、`userId`、`orderId`）→ 對應 `id` 欄位（pk）
- 其餘欄位依型別推斷（見下方型別對應表）
- 所有欄位預設 `[not null]`，除非有明確的可空需求

## 2. 型別對應

從 datatable 範例值推斷型別：

| 範例值 | DBML 型別 |
|--------|----------|
| `1`、`42` | `integer` |
| `"Alice"`、`"MacBook"` | `varchar` |
| 長文字（描述、內容） | `text` |
| `true`、`false` | `boolean` |
| `45000.5`、`0.8` | `decimal` |
| `2026-01-01` | `date` |
| `2026-01-01T00:00:00Z` | `timestamp` |
| 有限值域（`待付款`、`已付款`、`已取消`） | `enum`（見下方 Enum 萃取） |

---

# 從 Rule 推導約束

從 .feature 的 **前置（狀態）** 和 **前置（參數）** Rule 萃取約束：

| Rule 內容 | 對應約束 |
|-----------|---------|
| `<欄位>必須大於 0` | `[note: 'must be > 0']` 或 CHECK constraint |
| `<欄位>必須唯一` | `[unique]` |
| `<欄位>不可為空` | `[not null]` |
| `<欄位>長度不超過 N` | `[note: 'max length: N']` |
| `<欄位>必須為有效的 email` | `[note: 'must be valid email format']` |
| 狀態流轉限制（如「已取消訂單不可付款」） | 在 Table Note 中記錄，不在 DBML 直接表達 |

---

# Enum 萃取

有限值域的欄位提取為 Enum：

**來源一：datatable 欄位值**

若某欄位的範例值是有限集合（如 `status` 欄位的值為 `待付款`、`已付款`、`已取消`），提取為 Enum：

```dbml
Enum order_status {
  待付款  [note: 'pending payment']
  已付款  [note: 'paid']
  已取消  [note: 'cancelled']
}
```

**來源二：.activity 的 BRANCH guard 值**

若 .activity 的 DECISION guard 列出了某 Aggregate 屬性的可能值，同樣提取為 Enum。

---

# Relationship 偵測規則

掃描所有 Feature 的 datatable，找出跨資料表的 Aggregate 共現：

**規則**：若 Table A 的某個欄位名稱與 Table B 的 `id` 欄位對應（如 `orders` 表中的 `userId` 對應 `users.id`），建立關聯：

```dbml
// orders.userId 對應 users.id → many-to-one
Ref: orders.userId > users.id
```

**多對多**：若需要 junction table（如使用者與課程的多對多），新增 junction table：

```dbml
Table user_courses {
  userId   integer  [ref: > users.id]
  courseId integer  [ref: > courses.id]

  indexes {
    (userId, courseId) [pk]
  }
}
```

---

# 便條紙格式（強制規範）

**所有便條紙一律使用 CiC 格式，包在 DBML 原生行尾 comment 內：**

```
// CiC(<CATEGORY>): 說明文字
```

**嚴禁使用任何其他格式**，包含但不限於：
- `// <!-- ?N[類型] ... -->` ❌（舊格式）
- `// (待澄清)` ❌
- `// TODO` ❌

理由：系統使用 Grep 工具搜尋 `CiC\(` 統一掃描所有視圖（`.activity`、`.feature`、`erm.dbml`、`api.yml`）的未解便條紙，非此格式的標記將被漏掉。

**5 種分類：**

| 分類 | 代碼 | 使用時機 |
|------|------|---------|
| Ambiguity | `AMB` | 需求存在多種合理解讀 |
| Assumption | `ASM` | AI 做了一個未經確認的選擇 |
| Gap | `GAP` | 資訊完全缺失 |
| Conflict | `CON` | 需求之間存在矛盾 |
| Boundary | `BDY` | 範圍邊界不明確 |

**範例：**
```dbml
Table orders {
  status  varchar  // CiC(ASM): 假設狀態值為 待付款/已付款/已取消，需確認是否完整
}
```

---

# 便條紙規則

在以下情況於 erm.dbml 對應位置加上便條紙（行尾 `// CiC(<CATEGORY>): 內容`）：

| 代碼 | 何時標記 |
|------|---------|
| `GAP` | 無法從 .feature 確定欄位型別或長度時 |
| `ASM` | 推斷了 Enum 值域但不確定是否完整時 |
| `AMB` | 關聯方向不確定（one-to-one vs one-to-many）時 |
| `CON` | 同一欄位在不同 Feature 的 datatable 中型別不一致時 |

---

# Strategy Guard（逆向回饋）

在生成 erm.dbml 時，若發現以下情況，向協調器回報並觸發 Strategy Guard：

1. **Aggregate 結構衝突**：正規化發現某個 Aggregate 應該拆分（如訂單明細應獨立成 `order_items` 表），而現有 .feature 中的 Background datatable 違反了這個設計 → 需要回到 Feature 層修正
2. **缺少必要 Aggregate**：某個關聯需要 Aggregate B 存在，但沒有任何 .feature 定義了 Aggregate B → 需要回到 Strategic 補充相關 Feature

---

# 完成條件

所有 .feature 中出現的 Aggregate 均有對應資料表，所有欄位有明確型別，所有關聯已標示，無便條紙、無模糊約束，erm.dbml 可被 DBML parser 解析。
