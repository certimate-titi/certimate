---
name: aibdd.auto.python.e2e.refactor
description: Python E2E Stage 4：重構階段。在測試保護下改善程式碼品質，小步前進，嚴格遵守 /aibdd.auto.python.code-quality 規範。可被 /python-e2e 調用，也可獨立使用。
user-invocable: true
args-config: arguments-template.yml
argument-hint: "[feature-file]"
input: ${PY_STEPS_DIR}/**/*.py, ${PY_MODELS_DIR}/**/*.py, ${PY_SERVICES_DIR}/**/*.py, ${PY_API_DIR}/**/*.py
output: 重構後的程式碼（測試持續通過）
---

# 角色

重構守護者。在保持測試通過（綠燈）的前提下，改善程式碼品質。

---

# 入口

## 被 /python-e2e 調用時

接收參數 `FEATURE_FILE`，直接進入重構流程。

## 獨立使用時

詢問目標範圍：

```
請指定要重構的範圍：
1. 特定 Feature 相關的程式碼（提供 feature file 路徑）
2. 全域重構（所有已通過測試的程式碼）

（例如：${PY_TEST_FEATURES_DIR}/01-增加影片進度.feature）
```

---

# 重構流程

```
1. 執行測試，確認目前是綠燈
2. 識別一個小的重構點
3. 執行重構
4. 執行測試，確認仍是綠燈
5. 若失敗，立即回滾
6. 重複步驟 2-5
```

**測試指令**：
```bash
# 重構前後都必須執行
behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore
```

---

# 核心原則

## 1. 測試保護原則
每次重構後立即執行測試，確保全部通過。若失敗則立即回滾。

## 2. 小步前進原則
一次只做一個小重構，避免一次改動過多。

## 3. 不強行重構原則
只在真正有改善空間時才重構。程式碼已清晰簡潔時保持原樣，遵循 YAGNI 原則。

## 4. 清除測試 Warnings
盡可能清除所有測試 warnings，保持測試輸出乾淨。

---

# 遵守規範

重構時**嚴格遵守** /aibdd.auto.python.code-quality 的每一條規範。

---

# 重構檢查清單

執行重構時確認：

## 流程
- [ ] 重構前測試是綠燈
- [ ] 每次小重構後執行測試
- [ ] 重構後測試仍是綠燈
- [ ] 所有測試 warnings 已清除

## 規範遵守
- [ ] 嚴格遵守 /aibdd.auto.python.code-quality 的每一條規範

---

# 重構原則

**應該做：**
- 在測試保護下進行重構
- 小步前進，一次一個重構點
- 嚴格遵守各項規範
- 清除所有測試 warnings

**不應該做：**
- 沒有測試保護就重構
- 一次改動過多
- 違反任何規範
- 強行重構已經清晰的程式碼

---

# 完成條件

- [ ] 重構前執行 `behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore` 確認綠燈
- [ ] 每次小重構後執行測試確認仍為綠燈
- [ ] 所有測試 warnings 已清除
- [ ] 嚴格遵守 /aibdd.auto.python.code-quality 的每一條規範
- [ ] 重構後執行 `behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore` 確認所有測試通過
- [ ] 測試輸出乾淨（無 warnings、無 deprecation notices）
