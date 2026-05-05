/**
 * @file QuotaBadge.tsx — 配額計數小徽章（L-quota）
 *
 * 顯示「已用 / 上限」與三種狀態（綠色 / 80% 警告 / 100% 達上限）。
 * 達上限時可直接連到 /account 升級頁。
 */
'use client';

import Link from 'next/link';
import type { QuotaKey } from '@/hooks/use-quota';
import { useQuotaGuard } from '@/hooks/use-quota';

export interface QuotaBadgeProps {
  /** 配額維度 key */
  quotaKey: QuotaKey;
  /** 顯示樣式：'inline' (緊湊) / 'pill' (圓角徽章) */
  variant?: 'inline' | 'pill';
  /** 自訂 className */
  className?: string;
  /** 達上限時是否顯示升級連結（預設 true） */
  showUpgradeLink?: boolean;
}

export default function QuotaBadge({ quotaKey, variant = 'inline', className = '', showUpgradeLink = true }: QuotaBadgeProps) {
  const guard = useQuotaGuard(quotaKey);

  if (!guard.ready) return null;
  if (guard.isUnlimited) {
    return variant === 'pill' ? (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 text-[10px] font-medium ${className}`}>
        ∞ 無限制
      </span>
    ) : (
      <span className={`text-[11px] text-indigo-600 font-medium ${className}`}>∞ 無限制</span>
    );
  }

  const tone = guard.is_blocked
    ? 'bg-rose-50 text-rose-700 border-rose-200'
    : guard.is_warning
      ? 'bg-amber-50 text-amber-700 border-amber-200'
      : 'bg-emerald-50 text-emerald-700 border-emerald-200';
  const inlineTone = guard.is_blocked
    ? 'text-rose-600'
    : guard.is_warning
      ? 'text-amber-600'
      : 'text-slate-500';

  if (variant === 'pill') {
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] font-medium ${tone} ${className}`}>
        {guard.used}/{guard.limit}
        {guard.is_blocked && showUpgradeLink && (
          <Link href="/account" className="ml-1 underline hover:text-rose-900">升級</Link>
        )}
      </span>
    );
  }

  return (
    <span className={`text-[11px] font-medium ${inlineTone} ${className}`}>
      {guard.used}/{guard.limit}
      {guard.is_blocked && showUpgradeLink && (
        <Link href="/account" className="ml-1 underline">升級</Link>
      )}
    </span>
  );
}
