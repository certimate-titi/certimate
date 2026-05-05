/**
 * @file use-quota.ts — 配額狀態 Hook（L-quota）
 *
 * 提供：
 * - useQuotaStatus(): 取得 5 維度配額狀態（含 SWR-like 快取與自動重整）
 * - useQuotaGuard(key): 單一維度的「是否可執行 + warning + 升級提示」
 *
 * 用法：
 *   const guard = useQuotaGuard('monthly_uploads');
 *   <button disabled={guard.isBlocked}>新增資源 ({guard.used}/{guard.limit})</button>
 *   {guard.isWarning && <Toast>剩餘 {guard.remaining} 次</Toast>}
 */
'use client';

import { useCallback, useEffect, useState } from 'react';
import { accountService } from '@/lib/api/services';
import type { QuotaStatusResponse, QuotaItem } from '@/types/api';

let _cachedStatus: QuotaStatusResponse | null = null;
let _lastFetchAt = 0;
const CACHE_TTL_MS = 30_000; // 30s 內共用快取
const _subscribers = new Set<(s: QuotaStatusResponse | null) => void>();

async function _fetchStatus(force = false): Promise<QuotaStatusResponse | null> {
  const now = Date.now();
  if (!force && _cachedStatus && (now - _lastFetchAt) < CACHE_TTL_MS) {
    return _cachedStatus;
  }
  try {
    const res = await accountService.getQuotaStatus();
    _cachedStatus = res;
    _lastFetchAt = now;
    _subscribers.forEach(fn => fn(res));
    return res;
  } catch {
    return _cachedStatus;
  }
}

export function useQuotaStatus(): {
  status: QuotaStatusResponse | null;
  loading: boolean;
  refetch: () => Promise<void>;
} {
  const [status, setStatus] = useState<QuotaStatusResponse | null>(_cachedStatus);
  const [loading, setLoading] = useState(!_cachedStatus);

  useEffect(() => {
    let mounted = true;
    const sub = (s: QuotaStatusResponse | null) => { if (mounted) setStatus(s); };
    _subscribers.add(sub);

    _fetchStatus().then(s => {
      if (mounted) {
        setStatus(s);
        setLoading(false);
      }
    });

    return () => {
      mounted = false;
      _subscribers.delete(sub);
    };
  }, []);

  const refetch = useCallback(async () => {
    setLoading(true);
    const s = await _fetchStatus(true);
    setStatus(s);
    setLoading(false);
  }, []);

  return { status, loading, refetch };
}

export type QuotaKey = 'monthly_uploads' | 'monthly_exams' | 'daily_ai_chats' | 'monthly_vision_pages' | 'max_file_size_mb';

/**
 * 取單一維度的守門狀態，方便按鈕直接 disabled / 顯示計數。
 */
export function useQuotaGuard(key: QuotaKey): QuotaItem & { isUnlimited: boolean; plan: string; ready: boolean; refetch: () => Promise<void> } {
  const { status, loading, refetch } = useQuotaStatus();
  const item = status?.quotas?.[key];
  const isUnlimited = !!status?.is_unlimited || (item?.limit === -1);

  return {
    label: item?.label ?? '',
    used: item?.used ?? 0,
    limit: item?.limit ?? -1,
    remaining: item?.remaining ?? -1,
    percentage: item?.percentage ?? 0,
    is_warning: !!item?.is_warning,
    is_blocked: !isUnlimited && !!item?.is_blocked,
    period: item?.period ?? 'monthly',
    action_hint: item?.action_hint ?? '',
    isUnlimited,
    plan: status?.plan ?? 'FREE',
    ready: !loading && !!status,
    refetch,
  };
}

/**
 * 重整全域快取（操作完成後呼叫，例如成功上傳資源後）。
 */
export async function invalidateQuotaCache() {
  await _fetchStatus(true);
}
