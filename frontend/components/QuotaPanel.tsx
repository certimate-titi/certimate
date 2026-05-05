/**
 * @file QuotaPanel.tsx — 帳號頁集中配額面板（L-quota）
 *
 * 顯示 5 維度配額：資源上傳、模擬測驗、AI 教練、PDF/圖像解析、單檔大小
 * 含進度條（綠 / 80% 黃 / 100% 紅）+ 升級 CTA。
 */
'use client';

import Link from 'next/link';
import { Sparkles } from 'lucide-react';
import { useQuotaStatus } from '@/hooks/use-quota';

const PLAN_LABELS: Record<string, string> = {
  FREE: '免費方案',
  PRO: 'PRO 方案',
  PRO_PLUS: 'PRO PLUS 方案',
  ULTRA: 'ULTRA 方案',
  EDU: 'EDU 教育方案',
  ADMIN_UNLIMITED: '管理者（無限制）',
};

const PERIOD_LABELS: Record<string, string> = {
  daily: '今日',
  monthly: '本月',
  constant: '單檔限制',
};

export default function QuotaPanel() {
  const { status, loading } = useQuotaStatus();

  if (loading) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-6 animate-pulse">
        <div className="h-5 w-32 bg-slate-200 rounded mb-4" />
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map(i => <div key={i} className="h-12 bg-slate-100 rounded" />)}
        </div>
      </div>
    );
  }

  if (!status) return null;

  const quotaList = [
    { key: 'monthly_uploads', q: status.quotas.monthly_uploads },
    { key: 'monthly_exams', q: status.quotas.monthly_exams },
    { key: 'daily_ai_chats', q: status.quotas.daily_ai_chats },
    { key: 'monthly_vision_pages', q: status.quotas.monthly_vision_pages },
    { key: 'max_file_size_mb', q: status.quotas.max_file_size_mb },
  ];

  const planLabel = PLAN_LABELS[status.plan] || status.plan;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4 gap-2">
        <div className="min-w-0">
          <h2 className="text-base sm:text-lg font-bold text-slate-900">配額狀態</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            目前方案：<span className="font-medium text-slate-700">{planLabel}</span>
            {status.period && !status.is_unlimited && <span className="ml-2">· {status.period}</span>}
          </p>
        </div>
        {!status.is_unlimited && (
          <Link
            href="/pricing"
            className="shrink-0 inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-emerald-500 text-white text-xs font-medium hover:bg-emerald-600 transition-colors"
          >
            <Sparkles className="h-3.5 w-3.5" />
            升級
          </Link>
        )}
      </div>

      <div className="space-y-3">
        {quotaList.map(({ key, q }) => {
          const isFileSize = key === 'max_file_size_mb';
          const unlimited = q.limit === -1;
          const periodLabel = PERIOD_LABELS[q.period] ?? '';

          return (
            <div key={key} className="rounded-xl border border-slate-100 bg-slate-50/50 p-3 sm:p-4">
              <div className="flex items-center justify-between mb-1.5 gap-2 flex-wrap">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-sm font-semibold text-slate-800 truncate">{q.label}</span>
                  {periodLabel && !unlimited && (
                    <span className="text-[10px] text-slate-400 bg-white px-1.5 py-0.5 rounded border border-slate-200 shrink-0">
                      {periodLabel}
                    </span>
                  )}
                </div>
                <div className="text-xs font-mono shrink-0">
                  {unlimited ? (
                    <span className="text-indigo-600 font-bold">∞ 無限制</span>
                  ) : isFileSize ? (
                    <span className="text-slate-700">≤ {q.limit} MB</span>
                  ) : (
                    <span className={
                      q.is_blocked ? 'text-rose-600 font-bold' :
                      q.is_warning ? 'text-amber-600 font-bold' :
                      'text-slate-700'
                    }>
                      {q.used}<span className="text-slate-400 mx-0.5">/</span>{q.limit}
                    </span>
                  )}
                </div>
              </div>

              {/* 進度條（file_size 與無限制不顯示） */}
              {!unlimited && !isFileSize && (
                <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      q.is_blocked ? 'bg-rose-500' :
                      q.is_warning ? 'bg-amber-500' :
                      'bg-emerald-500'
                    }`}
                    style={{ width: `${Math.min(100, q.percentage)}%` }}
                  />
                </div>
              )}

              <p className="text-[11px] text-slate-500 mt-1.5">{q.action_hint}</p>

              {q.is_blocked && (
                <div className="mt-2 flex items-center justify-between gap-2">
                  <span className="text-[11px] text-rose-600 font-medium">已達上限</span>
                  <Link href="/account" className="text-[11px] text-emerald-600 hover:text-emerald-700 underline font-medium">
                    升級方案解鎖 →
                  </Link>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
