/**
 * @file 知識圖譜進度聚合 hook。將原始扁平節點丟給 Web Worker 加權平均，
 * 主執行緒只負責收結果與更新 React state，避免大圖譜阻塞 UI。
 */
'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * 進度計算的扁平節點輸入。
 *
 * 由前端在 fetch 完知識圖譜後攤平為陣列，傳給 Worker 做父子聚合。
 */
export interface FlatNode {
  /** 節點 UUID。 */
  id: string;
  /** 父節點 UUID；root 節點為 `null`。 */
  parentId: string | null;
  /** 葉節點實際學習進度，範圍 [0, 1]。 */
  effectiveProgress: number;
  /** 權重（題目數或學習時長），用於加權平均。 */
  weight: number;
  /** 樹深度，root = 0。 */
  depth: number;
  /** 節點顯示名稱，僅用於 debug log。 */
  name: string;
}

/**
 * 單一節點聚合後的結果。
 *
 * 葉節點 `aggregatedProgress` 等於原始 `effectiveProgress`；
 * 中間節點則為子樹加權平均。
 */
export interface AggregatedNode {
  /** 聚合後進度 [0, 1]。 */
  aggregatedProgress: number;
  /** 直接子節點數（不含孫節點）。 */
  childCount: number;
  /** 衰減狀態，根據 progress 區間決定圖譜呈色。 */
  decayStatus: 'fresh' | 'decaying' | 'critical' | 'unseen';
}

/**
 * 使用 Web Worker 計算知識圖譜的聚合進度。
 *
 * 父節點進度 = Σ(子節點 effective_progress × weight) / total_weight。
 * 全部在客戶端計算，零 DB I/O；若瀏覽器不支援 Worker（SSR / 老瀏覽器）會
 * 自動降級為主執行緒運算（小資料量可接受）。
 *
 * @returns 物件含 `aggregated`（節點 ID → 聚合結果）、`computing`（運算中旗標）、
 *          `compute`（觸發運算的 callback）。
 *
 * @example
 * const { aggregated, computing, compute } = useProgressWorker();
 * useEffect(() => { compute(flatNodes); }, [flatNodes]);
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
