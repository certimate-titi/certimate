/**
 * Feature 33 — 成本監控中心型別定義
 * 對應後端 snake_case 欄位，前端顯示時才做轉換。
 */

export type BudgetScope =
  | 'AI_ANTHROPIC'
  | 'AI_GEMINI'
  | 'AI_VOYAGE'
  | 'GCP_TOTAL';

export type BudgetState = 'active' | 'warning' | 'degraded' | 'disabled';

export type AlertType = 'WARNING' | 'DEGRADE' | 'DISABLED';

export type GcpSyncStatus =
  | 'created'
  | 'updated'
  | 'skipped_non_gcp'
  | 'failed';

/** GET /admin/cost/summary 回應 */
export interface CostSummaryScopeItem {
  scope: BudgetScope;
  current_usd: number;
  limit_usd: number;
  percent: number;
  state: BudgetState;
}

export interface CostSummaryResponse {
  ok: true;
  scopes: CostSummaryScopeItem[];
  as_of: string;
}

/** GET /admin/cost/providers/{provider} 回應 */
export interface ProviderDetailResponse {
  ok: true;
  provider: string;
  scope: BudgetScope;
  input_tokens_total: number;
  output_tokens_total: number;
  cost_usd: number;
  limit_usd: number;
  daily_series: { date: string; cost_usd: number }[];
  quota_lock_enabled?: boolean;
  quota_remaining_usd?: number;
}

/** GET /admin/cost/gcp/services 回應 */
export interface GcpServiceCostItem {
  service_name: string;
  cost_usd: number;
}

export interface GcpServicesResponse {
  ok: true;
  total_usd: number;
  services: GcpServiceCostItem[];
  cached_at: string;
  period_start: string;
  period_end: string;
}

/** GET /admin/cost/trends 回應 */
export interface TrendDataPoint {
  date: string;
  ai_anthropic: number;
  ai_gemini: number;
  ai_voyage: number;
  gcp_total: number;
}

export interface TrendsResponse {
  ok: true;
  days: number;
  series: TrendDataPoint[];
}

/** PUT /admin/cost/budget request */
export interface UpdateBudgetRequest {
  scope: BudgetScope;
  monthly_limit_usd: number;
  reason: string;
}

/** POST /admin/cost/budget/global-scale request */
export interface GlobalScaleRequest {
  scale_factor?: number;
  target_total_usd?: number;
  reason: string;
}

/** POST /admin/cost/budget/override-disable request */
export interface OverrideDisableRequest {
  scope: BudgetScope;
  reason: string;
}

/** 通用 budget 修改回應 */
export interface BudgetUpdateResponse {
  ok: true;
  scope?: BudgetScope;
  monthly_limit_usd?: number;
  gcp_sync_status?: GcpSyncStatus;
  warning?: string;
  before?: Record<string, number>;
  after?: Record<string, number>;
  gcp_sync?: Record<string, GcpSyncStatus>;
}
