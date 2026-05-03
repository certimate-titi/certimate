/**
 * @file 路由 `/super-admin/cost-monitor` — 成本監控中心（Feature 33）。
 *
 * Super Admin 專屬：監控 GCS / Cloud Run / AI API token 等雲端成本，
 * 顯示日／月趨勢、異常告警、各服務拆分。延續 dashboard 的淺色主題。
 */
'use client';


import React, { useEffect, useState, useCallback } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { AlertTriangle, DollarSign, RefreshCw, Settings2, TrendingUp } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { costMonitorService } from '@/lib/api/services';
import type {
  CostSummaryScopeItem,
  BudgetScope,
  BudgetState,
  GcpServiceCostItem,
  TrendDataPoint,
} from '@/types/cost-monitor';

// ---------------------------------------------------------------------------
// 常數 / Helper
// ---------------------------------------------------------------------------

const SCOPE_LABELS: Record<BudgetScope, string> = {
  AI_ANTHROPIC: 'Anthropic',
  AI_GEMINI: 'Gemini',
  AI_VOYAGE: 'Voyage',
  GCP_TOTAL: 'GCP 總計',
};

const STATE_STYLES: Record<BudgetState, { bg: string; text: string; label: string }> = {
  active: { bg: 'bg-emerald-50', text: 'text-emerald-700', label: '正常' },
  warning: { bg: 'bg-amber-50', text: 'text-amber-700', label: '警告' },
  degraded: { bg: 'bg-orange-50', text: 'text-orange-700', label: '降級' },
  disabled: { bg: 'bg-rose-50', text: 'text-rose-700', label: '停用' },
};

function formatUsd(value: number | undefined | null): string {
  if (value == null || Number.isNaN(value)) return '$0.00';
  return `$${value.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function progressBarColor(percent: number): string {
  if (percent >= 100) return 'bg-rose-500';
  if (percent >= 80) return 'bg-orange-500';
  if (percent >= 50) return 'bg-amber-400';
  return 'bg-emerald-500';
}

function cardAccentIcon(scope: BudgetScope): string {
  const map: Record<BudgetScope, string> = {
    AI_ANTHROPIC: 'bg-violet-50 text-violet-600',
    AI_GEMINI: 'bg-blue-50 text-blue-600',
    AI_VOYAGE: 'bg-teal-50 text-teal-600',
    GCP_TOTAL: 'bg-amber-50 text-amber-600',
  };
  return map[scope];
}

// ---------------------------------------------------------------------------
// ScopeCard
// ---------------------------------------------------------------------------

function ScopeCard({
  item,
  onClickEdit,
}: {
  item: CostSummaryScopeItem;
  onClickEdit: (scope: BudgetScope) => void;
}) {
  const style = STATE_STYLES[item.state];
  const displayPercent = Math.min(item.percent, 999);
  return (
    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all">
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-xl ${cardAccentIcon(item.scope)}`}>
            <DollarSign className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              {SCOPE_LABELS[item.scope]}
            </p>
            <p className="text-2xl font-extrabold text-slate-900 tracking-tight mt-0.5">
              {formatUsd(item.current_usd)}
            </p>
          </div>
        </div>
        <span className={`text-xs font-semibold px-2 py-1 rounded-lg ${style.bg} ${style.text}`}>
          {style.label}
        </span>
      </div>

      <div className="mt-4">
        <div className="flex justify-between text-xs text-slate-500 mb-1.5">
          <span>當月使用率</span>
          <span className="font-semibold text-slate-700">{displayPercent.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
          <div
            className={`h-2 ${progressBarColor(item.percent)} transition-all`}
            style={{ width: `${Math.min(item.percent, 100)}%` }}
          />
        </div>
        <div className="text-xs text-slate-500 mt-2">
          月預算上限：<span className="font-semibold text-slate-700">{formatUsd(item.limit_usd)}</span>
        </div>
      </div>

      <button
        onClick={() => onClickEdit(item.scope)}
        className="mt-4 text-xs text-slate-500 hover:text-slate-900 flex items-center gap-1 transition-all"
      >
        <Settings2 className="w-3 h-3" /> 調整預算
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Budget Edit Modal
// ---------------------------------------------------------------------------

function BudgetEditModal({
  scope,
  currentLimit,
  onClose,
  onSaved,
}: {
  scope: BudgetScope;
  currentLimit: number;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [newLimit, setNewLimit] = useState(currentLimit.toString());
  const [reason, setReason] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    setError(null);
    const parsed = Number.parseFloat(newLimit);
    if (Number.isNaN(parsed) || parsed <= 0) {
      setError('請輸入有效的正數金額');
      return;
    }
    if (reason.trim().length < 2) {
      setError('請填寫修改原因（至少 2 字）');
      return;
    }
    setSaving(true);
    try {
      const resp = await costMonitorService.updateBudget({
        scope,
        monthly_limit_usd: parsed,
        reason: reason.trim(),
      });
      if (resp.warning) alert(`已儲存，但：${resp.warning}`);
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : '儲存失敗');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl p-6 max-w-md w-full border border-slate-200 shadow-xl">
        <h3 className="text-lg font-bold text-slate-900 mb-4">
          調整預算 — {SCOPE_LABELS[scope]}
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1.5">
              月預算上限 (USD)
            </label>
            <input
              type="number"
              step="0.01"
              value={newLimit}
              onChange={(e) => setNewLimit(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1.5">
              修改原因
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              placeholder="例如：業務成長、Q2 擴張"
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500"
            />
          </div>
          {error && (
            <div className="text-sm text-rose-600 flex items-center gap-1 bg-rose-50 px-3 py-2 rounded-lg border border-rose-200">
              <AlertTriangle className="w-4 h-4" />
              {error}
            </div>
          )}
        </div>
        <div className="flex justify-end gap-2 mt-6">
          <button
            onClick={onClose}
            disabled={saving}
            className="px-4 py-2 text-sm text-slate-600 hover:text-slate-900 transition-all"
          >
            取消
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 text-sm bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg shadow-sm shadow-emerald-500/20 transition-all disabled:opacity-50"
          >
            {saving ? '儲存中...' : '確認儲存'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Global Scale Modal
// ---------------------------------------------------------------------------

function GlobalScaleModal({
  onClose,
  onSaved,
}: {
  onClose: () => void;
  onSaved: () => void;
}) {
  const [mode, setMode] = useState<'scale' | 'target'>('scale');
  const [scalePercent, setScalePercent] = useState('20');
  const [targetTotal, setTargetTotal] = useState('1500');
  const [reason, setReason] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    setError(null);
    if (reason.trim().length < 2) {
      setError('請填寫原因');
      return;
    }
    setSaving(true);
    try {
      if (mode === 'scale') {
        const pct = Number.parseFloat(scalePercent);
        if (Number.isNaN(pct)) {
          setError('請輸入有效的百分比');
          return;
        }
        await costMonitorService.globalScale({
          scale_factor: 1 + pct / 100,
          reason: reason.trim(),
        });
      } else {
        const total = Number.parseFloat(targetTotal);
        if (Number.isNaN(total) || total <= 0) {
          setError('請輸入有效的金額');
          return;
        }
        await costMonitorService.globalScale({
          target_total_usd: total,
          reason: reason.trim(),
        });
      }
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : '儲存失敗');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl p-6 max-w-md w-full border border-slate-200 shadow-xl">
        <h3 className="text-lg font-bold text-slate-900 mb-4">整體預算調整</h3>
        <div className="flex gap-2 mb-4 text-xs font-medium bg-slate-100 rounded-lg p-1">
          <button
            onClick={() => setMode('scale')}
            className={`flex-1 py-2 rounded-md transition-all ${
              mode === 'scale' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'
            }`}
          >
            按比例 ±N%
          </button>
          <button
            onClick={() => setMode('target')}
            className={`flex-1 py-2 rounded-md transition-all ${
              mode === 'target' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'
            }`}
          >
            設目標總額
          </button>
        </div>
        <div className="space-y-4">
          {mode === 'scale' ? (
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1.5">
                調整百分比
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={scalePercent}
                  onChange={(e) => setScalePercent(e.target.value)}
                  className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500"
                />
                <span className="text-slate-500 font-semibold">%</span>
              </div>
              <div className="text-xs text-slate-500 mt-1.5">範圍：−50 至 +200</div>
            </div>
          ) : (
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1.5">
                目標總額 (USD)
              </label>
              <input
                type="number"
                step="1"
                value={targetTotal}
                onChange={(e) => setTargetTotal(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500"
              />
            </div>
          )}
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1.5">原因</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              placeholder="例如：Q2 業務擴張"
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500"
            />
          </div>
          {error && (
            <div className="text-sm text-rose-600 flex items-center gap-1 bg-rose-50 px-3 py-2 rounded-lg border border-rose-200">
              <AlertTriangle className="w-4 h-4" />
              {error}
            </div>
          )}
        </div>
        <div className="flex justify-end gap-2 mt-6">
          <button
            onClick={onClose}
            disabled={saving}
            className="px-4 py-2 text-sm text-slate-600 hover:text-slate-900 transition-all"
          >
            取消
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 text-sm bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg shadow-sm shadow-emerald-500/20 transition-all disabled:opacity-50"
          >
            {saving ? '儲存中...' : '確認儲存'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Trend Chart
// ---------------------------------------------------------------------------

function TrendChart({ data }: { data: TrendDataPoint[] }) {
  if (!data || data.length === 0) {
    return (
      <div className="h-72 flex items-center justify-center text-slate-400 text-sm">
        暫無趨勢資料（本月尚未使用 AI 服務）
      </div>
    );
  }
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
        <YAxis stroke="#64748b" fontSize={11} />
        <Tooltip
          contentStyle={{
            backgroundColor: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: '12px',
            boxShadow: '0 10px 25px -5px rgba(0,0,0,0.1)',
          }}
          labelStyle={{ color: '#0f172a', fontWeight: 600 }}
        />
        <Legend />
        <Area type="monotone" dataKey="ai_anthropic" stackId="1" stroke="#8b5cf6" fill="#c4b5fd" />
        <Area type="monotone" dataKey="ai_gemini" stackId="1" stroke="#3b82f6" fill="#93c5fd" />
        <Area type="monotone" dataKey="ai_voyage" stackId="1" stroke="#14b8a6" fill="#5eead4" />
        <Area type="monotone" dataKey="gcp_total" stackId="1" stroke="#f59e0b" fill="#fcd34d" />
      </AreaChart>
    </ResponsiveContainer>
  );
}

// ---------------------------------------------------------------------------
// GCP Service Breakdown
// ---------------------------------------------------------------------------

function GcpServiceBreakdown({
  services,
  totalUsd,
  error,
}: {
  services: GcpServiceCostItem[];
  totalUsd: number;
  error: string | null;
}) {
  if (error) {
    return (
      <div className="text-sm text-amber-700 p-4 bg-amber-50 rounded-lg border border-amber-200 flex items-start gap-2">
        <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
        <div>
          <div className="font-semibold">GCP 服務資料暫時無法取得</div>
          <div className="text-xs text-amber-600 mt-1">{error}</div>
        </div>
      </div>
    );
  }
  if (!services || services.length === 0) {
    return <div className="text-sm text-slate-400 py-4">暫無 GCP 服務資料</div>;
  }
  return (
    <div className="space-y-3">
      {services.map((svc) => {
        const pct = totalUsd > 0 ? (svc.cost_usd / totalUsd) * 100 : 0;
        return (
          <div
            key={svc.service_name}
            className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0"
          >
            <div className="flex-1 mr-4">
              <div className="text-sm font-medium text-slate-700">{svc.service_name}</div>
              <div className="w-full bg-slate-100 rounded-full h-1 mt-1.5">
                <div
                  className="h-1 bg-blue-500 rounded-full"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
            <div className="text-sm font-mono font-semibold text-slate-900">
              {formatUsd(svc.cost_usd)}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function CostMonitorPage() {
  const router = useRouter();
  const { loading: authLoading, isAuthenticated, isSuperAdmin } = useAuth();
  // SUPER_ADMIN-only：高等設定（成本監控涉預算/AI 用量）
  useEffect(() => {
    if (!authLoading && isAuthenticated && !isSuperAdmin) {
      router.replace('/super-admin/dashboard');
    }
  }, [authLoading, isAuthenticated, isSuperAdmin, router]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scopes, setScopes] = useState<CostSummaryScopeItem[]>([]);
  const [trends, setTrends] = useState<TrendDataPoint[]>([]);
  const [gcpServices, setGcpServices] = useState<GcpServiceCostItem[]>([]);
  const [gcpTotal, setGcpTotal] = useState(0);
  const [gcpError, setGcpError] = useState<string | null>(null);
  const [editingScope, setEditingScope] = useState<BudgetScope | null>(null);
  const [showGlobalModal, setShowGlobalModal] = useState(false);

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [summary, trendsResp] = await Promise.all([
        costMonitorService.getSummary(),
        costMonitorService.getTrends(30),
      ]);
      setScopes(summary.scopes || []);
      setTrends(trendsResp.series || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : '載入失敗');
    } finally {
      setLoading(false);
    }

    try {
      const gcp = await costMonitorService.getGcpServices();
      setGcpServices(gcp.services || []);
      setGcpTotal(gcp.total_usd || 0);
      setGcpError(null);
    } catch (e) {
      setGcpError(e instanceof Error ? e.message : 'GCP 服務資料暫時無法取得');
    }
  }, []);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const totalCurrent = scopes.reduce((sum, s) => sum + s.current_usd, 0);
  const totalLimit = scopes.reduce((sum, s) => sum + s.limit_usd, 0);
  const overallPercent = totalLimit > 0 ? (totalCurrent / totalLimit) * 100 : 0;

  if (authLoading || !isAuthenticated || !isSuperAdmin) {
    return (
      <div className="p-8 text-slate-500 text-sm">
        {authLoading ? '載入中⋯' : '需要 SUPER_ADMIN 權限。'}
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto bg-slate-50 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <DollarSign className="w-6 h-6 text-emerald-500" />
            成本監控中心
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            當月總花費{' '}
            <span className="font-semibold text-slate-700">{formatUsd(totalCurrent)}</span> / 預算{' '}
            <span className="font-semibold text-slate-700">{formatUsd(totalLimit)}</span>
            <span className="ml-2">({overallPercent.toFixed(1)}%)</span>
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowGlobalModal(true)}
            className="px-4 py-2 text-sm bg-white border border-slate-200 rounded-lg text-slate-700 font-medium hover:bg-slate-50 shadow-sm transition-all flex items-center gap-1.5"
          >
            <TrendingUp className="w-4 h-4" />
            整體調整
          </button>
          <button
            onClick={loadAll}
            disabled={loading}
            className="px-4 py-2 text-sm bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg shadow-sm shadow-emerald-500/20 transition-all flex items-center gap-1.5 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            重新整理
          </button>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-6 p-4 bg-rose-50 border border-rose-200 rounded-2xl text-rose-700 flex items-start gap-2">
          <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">載入失敗</div>
            <div className="text-sm text-rose-600 mt-1">{error}</div>
            {String(error).includes('SUPER_ADMIN') && (
              <div className="text-xs text-rose-500 mt-2">
                此頁面僅 Super Admin 可存取，請用 <code className="bg-rose-100 px-1 rounded">super@certimate.com</code> 登入
              </div>
            )}
          </div>
        </div>
      )}

      {/* Scope cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        {loading && scopes.length === 0 ? (
          <div className="col-span-full text-center text-slate-400 py-12">載入中...</div>
        ) : scopes.length === 0 && !error ? (
          <div className="col-span-full text-center text-slate-400 py-12">尚未設定任何預算</div>
        ) : (
          scopes.map((item) => (
            <ScopeCard
              key={item.scope}
              item={item}
              onClickEdit={(s) => setEditingScope(s)}
            />
          ))
        )}
      </div>

      {/* Trends chart */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm mb-6">
        <h2 className="font-bold text-slate-900 flex items-center gap-2 mb-5">
          <TrendingUp className="w-5 h-5 text-blue-500" />
          30 天成本趨勢
        </h2>
        <TrendChart data={trends} />
      </div>

      {/* GCP Services */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm mb-6">
        <h2 className="font-bold text-slate-900 mb-5 flex items-center gap-2">
          GCP 服務分類（當月）
        </h2>
        <GcpServiceBreakdown
          services={gcpServices}
          totalUsd={gcpTotal}
          error={gcpError}
        />
      </div>

      {/* Edit Modals */}
      {editingScope && (
        <BudgetEditModal
          scope={editingScope}
          currentLimit={
            scopes.find((s) => s.scope === editingScope)?.limit_usd || 0
          }
          onClose={() => setEditingScope(null)}
          onSaved={() => {
            setEditingScope(null);
            loadAll();
          }}
        />
      )}

      {showGlobalModal && (
        <GlobalScaleModal
          onClose={() => setShowGlobalModal(false)}
          onSaved={() => {
            setShowGlobalModal(false);
            loadAll();
          }}
        />
      )}
    </div>
  );
}
