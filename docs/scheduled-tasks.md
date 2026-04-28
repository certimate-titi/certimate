# CertiMate 自動排程任務清單

> 最後更新：2026-04-28
>
> 所有排程透過 MCP `scheduled-tasks` 執行（user-local cron）。
> Cron 表達式以使用者 **local time（Asia/Taipei UTC+8）** 計算，非 UTC。
> 管理介面：Claude Code 側欄「Scheduled」區塊，或用 MCP `list_scheduled_tasks` / `update_scheduled_task` / `delete_scheduled_task`。

## 排程一覽

| Task ID | Cron（本地時間）| 用途 | 失敗時行為 | 建立來源 |
|---------|----------------|------|------------|----------|
| `exam-bank-pdf-check` | 每日 03:02 | 檢查考古題 PDF 未轉換並啟動 LLM 轉換 | 重試下個週期 | exam-crawler skill |
| `daily-spec-drift` | 每日 04:05 | 跑 `scripts/spec_drift_check.py` 偵測 deprecated feature 殘留 | Push notification ＋ `docs/spec-drift-check-{date}.md` 詳細報告 | titi-commander |
| `weekly-exam-crawl` | 每週五 02:01 | 自動爬取考古題網站，檢查是否有新增考試題目 | 寫入 logs，下週重跑 | exam-crawler skill |
| `weekly-feature-coverage` | 每週日 09:02 | 跑 `scripts/lint_feature_tags.py` + `spec_drift_check.py` + spec 統計，產出週報 `docs/feature-coverage-weekly-{date}.md` | Push notification（若 violation > 0） | titi-commander |
| `monthly-doc-review` | 每月第一個週一 09:00 | 檢查所有規格文件是否需要更新 | 寫入 `docs/todo-check-{datetime}.md` 與 `docs/todo-processing-{datetime}.md` | titi-commander |

## 觸發機制 vs 手動工具對照

| 機制 | 觸發 | 範圍 |
|------|------|------|
| MCP `scheduled-tasks` | 上表 cron | 整個 Claude Code 環境 |
| GitHub Actions（`deploy-gcp.yml`）| `git push origin main` | 雲端部署 |
| `scripts/heartbeat.sh` | **手動** `bash scripts/heartbeat.sh` | TiTi 雙心跳報告 |
| `scripts/spec_drift_check.py` | **手動 + daily-spec-drift 排程** | Spec 殘留掃描 |
| `scripts/lint_feature_tags.py` | **手動 + weekly-feature-coverage 排程** | BDD tag 一致性 |
| `scripts/titi_ops.py` | **手動** | 任務管理 CLI |
| `scripts/archive_tasks.sh` | **手動** | 歸檔 7 天前任務 |

## 排程任務管理

### 列出全部
```bash
# 在 Claude Code 內：用 MCP tool list_scheduled_tasks
```

### 新增 / 更新
```bash
# 新增：MCP tool create_scheduled_task
# 更新：MCP tool update_scheduled_task（用 taskId）
# 啟停：在 Scheduled 側欄 toggle，或 update_scheduled_task --enabled false
```

### 排程設計原則

1. **凌晨集中**：03:00–05:00 跑批次任務，避開使用者活躍時段
2. **每日 vs 每週**：高敏感度（drift / 殘留）每日；統計性週報每週
3. **失敗通知**：透過 Claude Code PushNotification，董事會（Simon）即時看到
4. **冪等性**：每個排程腳本必須冪等（重複執行結果一致），避免時區誤差導致重複處理
5. **Token 預算**：每次執行 < 5K token，避免費用爆走

## 已 deprecated 排程

無（截至 2026-04-28）。

## 加入新排程的 SOP

1. 確認需要排程（不是一次性 ScheduleWakeup）
2. 用 MCP `create_scheduled_task` 建立
3. 將排程加進此檔案
4. commit `docs/scheduled-tasks.md`
5. 跑一次 manually 驗證
6. 觀察首次自動執行的結果
