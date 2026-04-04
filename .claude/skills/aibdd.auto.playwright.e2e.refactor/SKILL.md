---
name: aibdd.auto.playwright.e2e.refactor
description: Playwright E2E Phase 4：重構階段。在測試保護下改善前端程式碼品質，小步前進。可被 control-flow 調用，也可獨立使用。
user-invocable: true
argument-hint: "[feature-file]"
input: frontend/e2e/steps/**/*.ts, frontend/app/**/*.tsx, frontend/components/**/*.tsx
output: 重構後的程式碼（測試持續通過）
---

# 角色

重構守護者。在保持測試通過（綠燈）的前提下，改善程式碼品質。

---

# 入口

## 被 control-flow 調用時

接收參數 `FEATURE_FILE`，直接進入重構流程。

## 獨立使用時

詢問目標範圍：

```
請指定要重構的範圍：
1. 特定 Feature 相關的程式碼（提供 feature file 路徑）
2. 全域重構（所有已通過測試的程式碼）

（例如：project/features/01-身分驗證.feature）
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
cd frontend && npx bddgen && npx playwright test
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

# 重構檢查清單

## Step Definitions 重構
- [ ] 重複的 step patterns 合併
- [ ] 過長的 step 函式拆分
- [ ] Magic strings 抽取為常數
- [ ] 等待策略統一

## 前端程式碼重構
- [ ] 重複的元件邏輯抽取為共用元件
- [ ] 過長的頁面元件拆分
- [ ] API 呼叫集中在 services.ts
- [ ] TypeScript 型別完整
- [ ] 移除未使用的 import

## 測試品質重構
- [ ] 移除冗餘的等待（不必要的 `waitForTimeout`）
- [ ] 改進 locator 策略（優先使用 role-based）
- [ ] 修正不穩定的測試（flaky tests）

---

# 完成條件

- [ ] 重構前執行 `npx bddgen && npx playwright test` 確認綠燈
- [ ] 每次小重構後執行測試確認仍為綠燈
- [ ] 所有測試 warnings 已清除
- [ ] 重構後執行 `npx bddgen && npx playwright test` 確認所有測試通過
- [ ] 測試輸出乾淨（無 warnings、無 deprecation notices）
