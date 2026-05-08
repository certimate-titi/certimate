/**
 * useNodeScaffoldData — 統一節點鷹架資料 hook（Sprint 1 T06）
 *
 * 解決：ScaffoldMaterial / ScaffoldNotebook / ScaffoldReplayCard 三元件
 * 各自 fetch 同一個 nodeId 的問題（同一 nodeId 切換時 3 次重複 API 呼叫）。
 *
 * 用途：
 * - 既有元件可漸進改用此 hook（opt-in，不強制）
 * - 新元件 RetrievalCard / InlinePractice 直接用此 hook
 *
 * 含模組級 cache（per-process），nodeId 切換不重新 fetch；
 * 提供 invalidate 在使用者作答後手動失效。
 */

import { useCallback, useEffect, useState } from 'react';

import { knowledgeService, type NodeScaffoldsResponse } from '@/lib/api/services';

interface CacheEntry {
  data: NodeScaffoldsResponse;
  fetchedAt: number;
}

const CACHE_TTL_MS = 60_000; // 1 分鐘
const cache = new Map<string, CacheEntry>();
const inflight = new Map<string, Promise<NodeScaffoldsResponse>>();

export interface UseNodeScaffoldDataResult {
  data: NodeScaffoldsResponse | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

async function fetchWithDedup(nodeId: string): Promise<NodeScaffoldsResponse> {
  const cached = cache.get(nodeId);
  if (cached && Date.now() - cached.fetchedAt < CACHE_TTL_MS) {
    return cached.data;
  }
  const existing = inflight.get(nodeId);
  if (existing) return existing;

  const promise = knowledgeService
    .getNodeScaffolds(nodeId)
    .then((data) => {
      cache.set(nodeId, { data, fetchedAt: Date.now() });
      return data;
    })
    .finally(() => {
      inflight.delete(nodeId);
    });
  inflight.set(nodeId, promise);
  return promise;
}

/**
 * 失效 cache（作答 / 互動後呼叫）。傳 null 失效全部。
 */
export function invalidateNodeScaffoldCache(nodeId: string | null = null): void {
  if (nodeId) cache.delete(nodeId);
  else cache.clear();
}

export function useNodeScaffoldData(nodeId: string | null): UseNodeScaffoldDataResult {
  const [data, setData] = useState<NodeScaffoldsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (nid: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchWithDedup(nid);
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'scaffold 載入失敗');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!nodeId) {
      setData(null);
      return;
    }
    void load(nodeId);
  }, [nodeId, load]);

  const refetch = useCallback(async () => {
    if (!nodeId) return;
    cache.delete(nodeId);
    await load(nodeId);
  }, [nodeId, load]);

  return { data, loading, error, refetch };
}
