'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

export interface FlatNode {
  id: string;
  parentId: string | null;
  effectiveProgress: number;
  weight: number;
  depth: number;
  name: string;
}

export interface AggregatedNode {
  aggregatedProgress: number;
  childCount: number;
  decayStatus: 'fresh' | 'decaying' | 'critical' | 'unseen';
}

/**
 * Hook: 使用 Web Worker 計算知識圖譜的聚合進度。
 *
 * 父節點進度 = Σ(子節點 effective_progress × weight) / total_weight
 * 全部在客戶端計算，零 DB I/O。
 */
export function useProgressWorker() {
  const workerRef = useRef<Worker | null>(null);
  const [aggregated, setAggregated] = useState<Record<string, AggregatedNode>>({});
  const [computing, setComputing] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    try {
      workerRef.current = new Worker('/workers/progress-aggregator.js');
      workerRef.current.onmessage = (e) => {
        if (e.data.type === 'RESULT') {
          setAggregated(e.data.aggregated);
          setComputing(false);
        }
      };
      workerRef.current.onerror = () => {
        setComputing(false);
      };
    } catch {
      // Worker 不支援時（SSR or old browser），靜默降級
    }

    return () => {
      workerRef.current?.terminate();
    };
  }, []);

  const compute = useCallback((nodes: FlatNode[]) => {
    if (workerRef.current) {
      setComputing(true);
      workerRef.current.postMessage({ type: 'AGGREGATE', nodes });
    } else {
      // Fallback: 不用 worker，直接在主線程算（小數據量可接受）
      const result: Record<string, AggregatedNode> = {};
      for (const node of nodes) {
        result[node.id] = {
          aggregatedProgress: node.effectiveProgress,
          childCount: 0,
          decayStatus: node.effectiveProgress >= 0.7 ? 'fresh' :
                       node.effectiveProgress >= 0.4 ? 'decaying' :
                       node.effectiveProgress > 0 ? 'critical' : 'unseen',
        };
      }
      setAggregated(result);
    }
  }, []);

  return { aggregated, computing, compute };
}
