# LLM 毛利儀表板 Spec（議題 B1 / Sprint 8）

- 提案日：2026-05-08
- 範圍：訂閱方案毛利率分析 + LLM API 成本攤提到 per-user / per-plan
- 不在範圍：自動定價、自動限流（本期僅產報表 + 預警）
- 匯率假設：1 USD = 32 TWD（以當月 GCP Billing 結帳匯率為準）

---

## 1. 單用戶月成本公式

每位 active user 月成本 `C_user(m) = Σ Variable_i + Allocated_Fixed`。
分項、來源、聚合粒度如下：

| 成本項 | 公式 | 數據來源 | 聚合粒度 | 性質 |
|--------|------|---------|---------|------|
| Cloud Run（Web/API） | `(cpu_sec × $0.000024 + mem_GB_sec × $0.0000025 + req × $0.0000004) ÷ MAU` | GCP Billing Export `gcp_billing_export_v1_*`（service.description = 'Cloud Run'） | per_plan / monthly（MAU 攤提） | 共用固定 |
| Cloud Run Egress | `egress_GB × $0.40 ÷ MAU` | 同上 sku.description LIKE '%Network%Egress%' | per_plan / monthly | 共用固定 |
| GCS（resource 存放） | `bytes_stored_GB × $0.020 + Class-A ops × $0.005/1k` | GCP Billing service='Cloud Storage' | per_user / monthly（用 `resources.user_id` 帳到頭上） | 變動 |
| Cloud SQL（PostgreSQL 15 + pgvector） | `(vCPU_hr × $0.0413 + RAM_GB_hr × $0.007 + storage_GB × $0.17) ÷ MAU` | GCP Billing service='Cloud SQL' | per_plan / monthly | 共用固定 |
| Voyage Embedding | `Σ tokens_in × $0.00012/1k` | `ai_usage_ledger` where `feature='embedding'` | per_user / monthly | 變動 |
| Gemini 2.5 Pro（multi-modal parse / coach） | `Σ (tokens_in×$1.25 + tokens_out×$10.00)/1M` | `ai_usage_ledger` where `feature IN ('resource_parse','vision','coach')` | per_user / monthly | 變動 |
| Anthropic Sonnet 4.5（chat / 進階教練） | `Σ (tokens_in×$3 + tokens_out×$15)/1M` | `ai_usage_ledger` where `feature IN ('chat','advanced_coach')` | per_user / monthly | 變動 |
| 第三方（Firebase Auth、ECPay 抽成） | `Auth: $0.0055/MAU; ECPay: 售價 × 2.8%` | Firebase quota report + Invoice 表 | per_user / monthly | 變動 |

**攤提原則**：
- 變動成本（GCS / 三家 LLM）直接以 `user_id` 加總到該人頭。
- 共用固定成本（Cloud Run / SQL）以該月 MAU 平均攤提，再依 plan 加權（FREE 1×、PRO 1.2×、PRO_PLUS 1.8×、ULTRA 3×；權重來自 plan 配額比）。

---

## 2. 單元成本參數表（USD list price，2026-05 抓取）

| Provider / SKU | 單價 | 備註 |
|----------------|------|------|
| Voyage `voyage-3` embedding | $0.00012 / 1k tokens | input only |
| Gemini 2.5 Pro input (text) | $1.25 / 1M tokens | ≤200k context |
| Gemini 2.5 Pro output | $10.00 / 1M tokens | |
| Gemini 2.5 Pro vision page | ~$0.0025 / page | 1 page ≈ 258 input tokens + prompt |
| Anthropic Sonnet 4.5 input | $3.00 / 1M tokens | |
| Anthropic Sonnet 4.5 output | $15.00 / 1M tokens | |
| Cloud Run vCPU-sec | $0.000024 | tier 1 |
| Cloud Run GiB-sec | $0.0000025 | tier 1 |
| Cloud Run egress | $0.40 / GiB | asia → internet |
| Cloud SQL db-custom-2-7680 | $0.0826 / hr | ≈ $60/月 |
| Cloud SQL SSD storage | $0.17 / GiB-month | |
| GCS Standard (asia) | $0.020 / GiB-month | |
| Firebase Auth | $0.0055 / MAU after 50k free | 目前 < 50k 全免 |
| ECPay 信用卡 | 售價 × 2.8% | 月結 |

> 任何 list price 變動 ≥ 5% 必須觸發本表 re-issue + cost-impact 報告（見 CLAUDE.md 成本觸發條款）。

---

## 3. 毛利率計算（worst-case：100% 用滿配額）

假設參數（per 次平均）：
- chat: in 1.5k / out 0.8k tokens（Sonnet）
- exam 出題: in 4k / out 2k tokens（Gemini Pro）
- upload: 平均 8 MB → 1 次 parse(Gemini) ≈ in 30k + out 6k；embedding ≈ 50k tokens
- vision page: $0.0025
- 共用固定攤提（每 active user）：FREE $0.18 / PRO $0.22 / PRO_PLUS $0.32 / ULTRA $0.55

| 項目 | FREE | PRO_199 | PRO_PLUS_399 | ULTRA_1599 |
|------|------|---------|--------------|------------|
| Chat (30d × quota) | 90 → $0.42 | 900 → $4.16 | 6,000 → $27.7 | 上限 12,000* → $55.4 |
| Exam gen | 10 → $0.07 | 100 → $0.70 | 500 → $3.50 | 2,000* → $14.0 |
| Upload parse + embed | 5 → $1.13 | 50 → $11.3 | 200 → $45.0 | 500* → $112.5 |
| Vision pages | 0 | 0 | 50 → $0.13 | 500 → $1.25 |
| 共用固定攤提 | $0.18 | $0.22 | $0.32 | $0.55 |
| **合計 USD** | **$1.80** | **$16.6** | **$76.7** | **$183.7** |
| **合計 NT$** | **NT$58** | **NT$531** | **NT$2,454** | **NT$5,878** |
| 售價 NT$ | 0 | 199 | 399 | 1,599 |
| 毛利 NT$ | -58 | -332 | -2,055 | -4,279 |
| 毛利率 | N/A | -167% | -515% | -268% |

\* ULTRA 為 unlimited，估算採 fair-use cap（chat 400/天、exam 2000/月、upload 500/月）。

**讀數結論**：worst-case 全部赤字，必須仰賴典型用量（觀察值約配額的 15–25%）才獲利。儀表板核心目的就是**監控真實用量分佈，標出尾端重度用戶**。

典型用量假設（25% 配額利用率）下毛利率推估：

| 方案 | 典型成本 NT$ | 售價 NT$ | 毛利率 |
|------|-------------|---------|--------|
| FREE | 15 | 0 | -∞（補貼） |
| PRO_199 | 133 | 199 | 33% |
| PRO_PLUS_399 | 614 | 399 | -54% ⚠️ |
| ULTRA_1599 | 1,470 | 1,599 | 8% ⚠️ |

⚠️ **警示**：PRO_PLUS / ULTRA 即使典型用量也吃緊，需動態觀察 P75/P95。

---

## 4. 儀表板 UI 規格

路徑：`/admin/finance/gross-margin`（沿用 admin_finance router）。

### 上方 KPI Card（5 張）
1. **本月各 plan 平均毛利 NT$**（FREE 顯示「補貼成本」）
2. **整體毛利率%** + 30 天 sparkline
3. **LLM 成本 / 總成本佔比%**（觀察 LLM 是否成主導）
4. **新進付費用戶 7 日 LTV proxy**：`(7日累積毛利 / 新進人數) × (預估留存月數 6)`
5. **ULTRA fair-use 警戒線命中數**：本月超過 fair-use cap 的 ULTRA 用戶數

### 中段表格（Per-Plan Breakdown）
| Plan | Active 人數 | 平均月成本 | 售價 | 平均毛利 | 毛利率 | P95 成本 |
|------|------------|-----------|------|---------|--------|---------|

### 底段「最重度 Top 5 用戶」（每 plan 一張）
欄位：user_id（點擊到帳號詳情）、本月成本、佔該 plan 售價%、主要成本項（chat/upload/parse）、最後活躍日。

---

## 5. 預警閾值

| 等級 | 條件 | 動作 |
|------|------|------|
| INFO | 單用戶月成本 > 售價 50% | 寫 `cost_alert_log`，dashboard 黃標 |
| WARN | 單用戶月成本 > 售價 80% | Slack `#finance-alert`，客服標記觀察 |
| CRITICAL | 單用戶月成本 > 售價 120%（虧錢） | PagerDuty 通知 admin_finance owner，啟動 fair-use 通知信流程 |
| PLAN-LEVEL | 該 plan 月毛利率 < 10%（連續 2 週） | CTO + 財務評估調價或調配額 |
| GLOBAL | LLM 月成本 > 上月 ×1.4 | 觸發 cost_monitor budget_alert（既有機制） |

---

## 6. SQL Pseudo（後端 ticket 起點）

```sql
-- A. 每月 per-user LLM 成本（從 ai_usage_ledger）
WITH usd_rate AS (SELECT 32.0::numeric AS r),
unit AS (
  SELECT 'voyage_embed'::text AS k, 0.00012/1000 AS in_p, 0       AS out_p UNION ALL
  SELECT 'gemini_pro',           1.25/1e6,            10.00/1e6 UNION ALL
  SELECT 'anthropic_sonnet',     3.00/1e6,            15.00/1e6
)
SELECT
  l.user_id,
  date_trunc('month', l.created_at) AS month,
  SUM(
    CASE l.model_family
      WHEN 'voyage'    THEN l.tokens_in * (SELECT in_p FROM unit WHERE k='voyage_embed')
      WHEN 'gemini'    THEN l.tokens_in * (SELECT in_p FROM unit WHERE k='gemini_pro')
                          + l.tokens_out * (SELECT out_p FROM unit WHERE k='gemini_pro')
      WHEN 'anthropic' THEN l.tokens_in * (SELECT in_p FROM unit WHERE k='anthropic_sonnet')
                          + l.tokens_out * (SELECT out_p FROM unit WHERE k='anthropic_sonnet')
    END
  ) AS llm_cost_usd
FROM ai_usage_ledger l
GROUP BY l.user_id, month;

-- B. 每月 per-plan 共用固定攤提（GCP Billing）
WITH mau AS (
  SELECT u.subscription_plan AS plan, COUNT(DISTINCT u.id) AS users
  FROM users u
  JOIN ai_usage_ledger l ON l.user_id = u.id
   AND l.created_at >= date_trunc('month', now())
  GROUP BY u.subscription_plan
),
infra AS (
  SELECT SUM(cost) AS infra_usd
  FROM gcp_billing_export_v1
  WHERE service.description IN ('Cloud Run','Cloud SQL','Cloud Storage')
    AND usage_start_time >= date_trunc('month', now())
),
weight AS (
  SELECT * FROM (VALUES
    ('FREE',1.0),('PRO',1.2),('PRO_PLUS',1.8),('ULTRA',3.0),('EDU',1.5)
  ) w(plan, w)
)
SELECT m.plan,
       (i.infra_usd * w.w / SUM(w.w * m.users) OVER ()) AS infra_per_user_usd
FROM mau m
JOIN weight w USING (plan)
CROSS JOIN infra i;

-- C. 毛利率主表（A + B + 售價）
SELECT
  u.subscription_plan AS plan,
  AVG(a.llm_cost_usd + b.infra_per_user_usd) * (SELECT r FROM usd_rate) AS avg_cost_twd,
  CASE u.subscription_plan
    WHEN 'PRO' THEN 199 WHEN 'PRO_PLUS' THEN 399
    WHEN 'ULTRA' THEN 1599 ELSE 0 END AS price_twd
FROM users u
LEFT JOIN per_user_llm a USING (user_id)
LEFT JOIN per_plan_infra b ON b.plan = u.subscription_plan
GROUP BY u.subscription_plan;
```

---

## 7. 後端工程師 Ticket 起點

1. 新 Service `app/services/gross_margin_service.py`（繼承 BaseService）
2. 新 Router `app/api/admin_finance_margin.py`，掛 `/api/v1/admin/finance/gross-margin`
3. 沿用既有 `cost_monitor_service` 取 GCP Billing 部分
4. 新增 `cost_alert_log` table（Alembic 071，欄位：id, user_id, level, ratio, occurred_month, created_at）
5. BDD：`tests/features/admin_finance/gross_margin.feature`，至少含 1 個成功 + 1 個 403（非 admin）

— END —
