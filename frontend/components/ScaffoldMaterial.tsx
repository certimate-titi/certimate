/**
 * @file 學習鷹架教材元件——以快讀 / 深讀兩模式呈現節點對應的 takeaway 與 elaborative 鷹架。
 *       節點無正式鷹架（orphan）時，自動觸發 AI 補洞鷹架（OrphanScaffoldCard）。
 */
'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { BookOpen, Zap, Telescope, Send, Sparkles } from 'lucide-react';
import { knowledgeService, scaffoldService, orphanScaffoldService, type NodeScaffoldItem } from '@/lib/api/services';
import type { OrphanFillResponse, OrphanFillResult } from '@/types/api';
import OrphanScaffoldCard from '@/components/scaffold/OrphanScaffoldCard';
import OrphanScaffoldEmptyState from '@/components/scaffold/OrphanScaffoldEmptyState';
import MathContent from '@/components/MathContent';

/** 教材閱讀模式（Sprint 10 T92 — 後端 6 類前端歸併 3 類）：
 *  - anchor：讀前定錨（advance_organizer）— Ausubel subsumption
 *  - retrieval：重點檢索（takeaway + concept_extract）— Karpicke retrieval / Roediger testing effect
 *  - thinking：思考延伸（elaborative + strategy + pitfall）— Bloom analyze / metacognition / misconception correction
 */
export type ReadMode = 'anchor' | 'retrieval' | 'thinking';

/**
 * ScaffoldMaterial 的 props。
 */
export interface ScaffoldMaterialProps {
  /** 當前節點 ID；null 時依 fallbackResourceId 決定行為 */
  nodeId: string | null;
  /**
   * 來源資源 ID — 從 /resource-library 點「解析內容」進入時用以查資源層級鷹架，
   * 避開「統一樹節點 resource_id IS NULL」架構限制。
   * 當 node 查不到鷹架時自動 fallback 到資源層級。
   */
  fallbackResourceId?: string | null;
  /** 使用者是否為 PRO 訂戶（決定是否顯示付費牆） */
  isPro: boolean;
  /** 點擊「升級 PRO」按鈕的回呼 */
  onUpgradeClick?: () => void;
}

/**
 * 學習鷹架教材分頁。
 *
 * PRO 專屬功能；非 PRO 顯示付費牆，PRO 載入 `knowledgeService.getNodeScaffolds`，
 * 依 type 分為 takeaway（快讀）與 elaborative（深讀），深讀模式可送出回答並查看參考答案。
 *
 * @param props.nodeId - 節點 ID
 * @param props.isPro - 是否 PRO
 * @param props.onUpgradeClick - 升級回呼
 */
/** 最多輪詢 6 次（每次 5 秒，共 30 秒上限） */
const MAX_POLL_COUNT = 6;
const POLL_INTERVAL_MS = 5000;

export default function ScaffoldMaterial({ nodeId, fallbackResourceId, isPro, onUpgradeClick }: ScaffoldMaterialProps) {
  const [mode, setMode] = useState<ReadMode>('retrieval');  // 預設「重點檢索」（最常用）
  const [scaffolds, setScaffolds] = useState<NodeScaffoldItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paywall, setPaywall] = useState(false);

  // AI 補洞鷹架狀態
  const [orphanResult, setOrphanResult] = useState<OrphanFillResult | null>(null);
  const [orphanHidden, setOrphanHidden] = useState(false);
  const [orphanLoading, setOrphanLoading] = useState(false);
  const pollCountRef = useRef(0);
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  /** 停止輪詢計時器 */
  const stopPolling = useCallback(() => {
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  /** 觸發或輪詢 orphan fill */
  const fetchOrphanFill = useCallback(async (nId: string, isPolling = false) => {
    if (!isPolling) {
      setOrphanLoading(true);
      pollCountRef.current = 0;
    }
    try {
      const result = await orphanScaffoldService.getOrphanFill(nId);
      setOrphanResult(result);
      if ('status' in result && result.status === 'generating') {
        // 生成中 → 繼續輪詢
        pollCountRef.current += 1;
        if (pollCountRef.current < MAX_POLL_COUNT) {
          pollTimerRef.current = setTimeout(() => {
            fetchOrphanFill(nId, true);
          }, POLL_INTERVAL_MS);
        }
        // 超過 MAX_POLL_COUNT 就停止，保持 generating 狀態顯示
      }
      // ready / insufficient 都停止輪詢
    } catch {
      // API 404/403 等錯誤不影響正式鷹架空態
    } finally {
      if (!isPolling) setOrphanLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!nodeId && !fallbackResourceId) {
      setScaffolds([]);
      return;
    }
    if (!isPro) {
      setPaywall(true);
      setScaffolds([]);
      return;
    }
    setPaywall(false);
    setLoading(true);
    setError(null);

    const handleErr = (err: unknown) => {
      const e = err as { status?: number; message?: string };
      if (e.status === 403) setPaywall(true);
      else setError(e.message || '載入教材失敗');
    };

    // Sprint 10 T86：教育顧問鐵律「誤導 > 缺漏」— 節點無對應鷹架時不再 fallback
    // resource 全集（會顯示無關內容）。寧顯示空態也不誤導。
    // 例外：完全沒選節點（nodeId=null）時才用 resource 層級顯示總覽。
    const fetchPromise = nodeId
      ? knowledgeService.getNodeScaffolds(nodeId)
      : knowledgeService.getResourceScaffolds(fallbackResourceId!);

    fetchPromise
      .then((res) => setScaffolds(res.scaffolds || []))
      .catch(handleErr)
      .finally(() => setLoading(false));
  }, [nodeId, fallbackResourceId ?? null, isPro]);

  // 節點切換時重置 orphan 狀態並停止輪詢
  useEffect(() => {
    stopPolling();
    setOrphanResult(null);
    setOrphanHidden(false);
    setOrphanLoading(false);
    pollCountRef.current = 0;
  }, [nodeId, stopPolling]);

  // Unmount 時清理計時器
  useEffect(() => {
    return () => { stopPolling(); };
  }, [stopPolling]);

  useEffect(() => {
    // 條件：正式鷹架載入完成 + 結果為空 + 有 nodeId + isPro
    if (!loading && scaffolds.length === 0 && nodeId && isPro && !paywall) {
      fetchOrphanFill(nodeId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, scaffolds.length, nodeId, isPro, paywall]);

  if (!nodeId && !fallbackResourceId) {
    return (
      <div className="p-4 text-xs text-slate-400 text-center">
        <BookOpen className="h-6 w-6 mx-auto mb-2 text-slate-300" />
        點擊節點以查看教材
      </div>
    );
  }

  if (paywall) {
    return (
      <div className="p-4">
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-center">
          <Sparkles className="h-6 w-6 text-amber-500 mx-auto mb-2" />
          <p className="text-xs text-slate-700 font-semibold mb-1">學習教材為 PRO 專屬</p>
          <p className="text-[11px] text-slate-500 mb-3">升級解鎖 AI 智能提取的學習鷹架</p>
          <button
            onClick={onUpgradeClick}
            className="inline-flex items-center gap-1 bg-emerald-500 text-white px-3 py-1.5 rounded-lg text-xs font-bold hover:bg-emerald-600"
          >
            升級 PRO
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-4 flex items-center justify-center">
        <div className="w-4 h-4 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return <div className="p-4 text-xs text-rose-600">{error}</div>;
  }

  if (scaffolds.length === 0) {
    // A.3.4：依 orphan fill 狀態渲染
    if (orphanLoading) {
      return (
        <div className="p-4 flex items-center justify-center">
          <div className="w-4 h-4 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
        </div>
      );
    }

    if (orphanResult && !orphanHidden) {
      // 422 佐證不足
      if ('error' in orphanResult && orphanResult.error) {
        return (
          <div className="p-4">
            <OrphanScaffoldEmptyState
              mode="insufficient"
              evidenceCount={orphanResult.evidence_count}
            />
          </div>
        );
      }

      // 202 生成中
      if ('status' in orphanResult && orphanResult.status === 'generating') {
        return (
          <div className="p-4">
            <OrphanScaffoldEmptyState
              mode="generating"
              estimatedSeconds={(orphanResult as { estimated_seconds?: number }).estimated_seconds}
            />
          </div>
        );
      }

      // 200 ready：依信心分數決定是否渲染（< 31 顯示佐證不足）
      if ('status' in orphanResult && orphanResult.status === 'ready') {
        const ready = orphanResult as OrphanFillResponse;
        if (ready.confidence_score <= 30) {
          return (
            <div className="p-4">
              <OrphanScaffoldEmptyState mode="insufficient" evidenceCount={ready.evidence_count} />
            </div>
          );
        }
        return (
          <div className="p-4 overflow-y-auto">
            <OrphanScaffoldCard
              data={ready}
              onReported={() => setOrphanHidden(true)}
            />
          </div>
        );
      }
    }

    // 沒有 orphan 資料（API 失敗或 nodeId 為 null）— 顯示原始空態
    return (
      <div className="p-4 text-xs text-slate-400 text-center">
        <BookOpen className="h-6 w-6 mx-auto mb-2 text-slate-300" />
        此節點尚未對應到教材鷹架
      </div>
    );
  }

  // Sprint 10 T92：後端 6 類前端歸併 3 類顯示（教育顧問 §10.3）
  const anchors = scaffolds.filter((s) => s.type === 'advance_organizer');
  const retrievals = scaffolds.filter((s) => s.type === 'takeaway' || s.type === 'concept_extract');
  const thinkings = scaffolds.filter((s) =>
    s.type === 'elaborative' || s.type === 'strategy' || s.type === 'pitfall'
  );

  return (
    <div className="flex h-full flex-col">
      <div className="flex border-b border-slate-200 px-2 pt-2 gap-1 shrink-0">
        <button
          onClick={() => setMode('anchor')}
          disabled={anchors.length === 0}
          className={`flex items-center gap-1 px-3 py-1.5 rounded-t-md text-[11px] font-medium transition-colors ${
            mode === 'anchor' ? 'bg-violet-50 text-violet-700 border-b-2 border-violet-500'
              : anchors.length === 0 ? 'text-slate-300 cursor-not-allowed'
              : 'text-slate-500 hover:text-slate-700'
          }`}
          title="讀前定錨（Ausubel subsumption）"
        >
          🧭 定錨{anchors.length > 0 ? `（${anchors.length}）` : ''}
        </button>
        <button
          onClick={() => setMode('retrieval')}
          className={`flex items-center gap-1 px-3 py-1.5 rounded-t-md text-[11px] font-medium transition-colors ${
            mode === 'retrieval' ? 'bg-emerald-50 text-emerald-700 border-b-2 border-emerald-500' : 'text-slate-500 hover:text-slate-700'
          }`}
          title="重點檢索（Karpicke retrieval）"
        >
          <Zap className="h-3 w-3" /> 檢索{retrievals.length > 0 ? `（${retrievals.length}）` : ''}
        </button>
        <button
          onClick={() => setMode('thinking')}
          className={`flex items-center gap-1 px-3 py-1.5 rounded-t-md text-[11px] font-medium transition-colors ${
            mode === 'thinking' ? 'bg-amber-50 text-amber-700 border-b-2 border-amber-500' : 'text-slate-500 hover:text-slate-700'
          }`}
          title="思考延伸（Bloom analyze + 迷思警示）"
        >
          <Telescope className="h-3 w-3" /> 思考{thinkings.length > 0 ? `（${thinkings.length}）` : ''}
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-3">
        {mode === 'anchor' ? (
          <AnchorMode items={anchors} />
        ) : mode === 'retrieval' ? (
          <SpeedMode items={retrievals} />
        ) : (
          <DeepMode items={thinkings} />
        )}
      </div>
    </div>
  );
}

/** 讀前定錨模式（Ausubel subsumption）— violet 錨點卡片 */
function AnchorMode({ items }: { items: NodeScaffoldItem[] }) {
  if (items.length === 0) {
    return <p className="text-xs text-slate-400 text-center py-4">無讀前定錨內容</p>;
  }
  return (
    <ul className="space-y-2">
      {items.map((s) => (
        <li key={s.id} className="rounded-lg border border-violet-200 bg-violet-50/40 p-3">
          {s.chapter_heading && (
            <div className="text-[10px] font-semibold text-violet-600 mb-1">🧭 {s.chapter_heading}</div>
          )}
          <div className="text-xs text-slate-700 leading-relaxed"><MathContent>{s.content}</MathContent></div>
        </li>
      ))}
    </ul>
  );
}

/**
 * 快讀模式（內部子元件）——條列重點 takeaway 卡片，附頁碼。
 *
 * @param props.items - takeaway 鷹架清單
 */
function SpeedMode({ items }: { items: NodeScaffoldItem[] }) {
  if (items.length === 0) {
    return <p className="text-xs text-slate-400 text-center py-4">無快讀卡片</p>;
  }
  return (
    <ul className="space-y-2">
      {items.map((s) => (
        <li key={s.id} className="rounded-lg border border-slate-200 bg-white p-3">
          {s.chapter_heading && (
            <div className="text-[10px] font-semibold text-emerald-600 mb-1">{s.chapter_heading}</div>
          )}
          <div className="text-xs text-slate-700 leading-relaxed"><MathContent>{s.content}</MathContent></div>
          {(s.page_start || s.page_end) && (
            <div className="mt-1.5 text-[10px] text-slate-400">
              頁 {s.page_start ?? '-'}{s.page_end && s.page_end !== s.page_start ? `–${s.page_end}` : ''}
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}

/**
 * 深讀模式（內部子元件）——展開 elaborative 提問清單。
 *
 * @param props.items - elaborative 鷹架清單
 */
function DeepMode({ items }: { items: NodeScaffoldItem[] }) {
  if (items.length === 0) {
    return <p className="text-xs text-slate-400 text-center py-4">無深讀提問</p>;
  }
  return (
    <ul className="space-y-3">
      {items.map((s) => (
        <DeepItem key={s.id} item={s} />
      ))}
    </ul>
  );
}

/**
 * 單一深讀提問項（內部子元件）。
 *
 * 提供 textarea 收集使用者回答，呼叫 `scaffoldService.submitResponse` 儲存後解鎖參考答案。
 *
 * @param props.item - 單筆 elaborative 鷹架
 */
function DeepItem({ item }: { item: NodeScaffoldItem }) {
  const [response, setResponse] = useState(item.user_response || '');
  const [saved, setSaved] = useState(Boolean(item.user_response));
  const [saving, setSaving] = useState(false);
  const [reveal, setReveal] = useState(Boolean(item.user_response));
  const [err, setErr] = useState<string | null>(null);

  async function handleSubmit() {
    if (!response.trim() || saving) return;
    setSaving(true);
    setErr(null);
    try {
      await scaffoldService.submitResponse(item.id, response.trim());
      setSaved(true);
      setReveal(true);
    } catch (e) {
      setErr((e as Error).message || '儲存失敗');
    } finally {
      setSaving(false);
    }
  }

  return (
    <li className="rounded-lg border border-slate-200 bg-white p-3">
      {item.chapter_heading && (
        <div className="text-[10px] font-semibold text-emerald-600 mb-1">{item.chapter_heading}</div>
      )}
      <div className="text-xs font-semibold text-slate-800 mb-2 leading-relaxed"><MathContent>{item.content}</MathContent></div>
      <div className="relative">
        <textarea
          value={response}
          onChange={(e) => setResponse(e.target.value)}
          placeholder="用自己的話試著回答..."
          rows={3}
          className="w-full rounded-md border border-slate-200 bg-slate-50 px-2 py-1.5 text-[11px] text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none"
          disabled={saving}
        />
        <button
          onClick={handleSubmit}
          disabled={!response.trim() || saving}
          className="absolute right-1 bottom-1 inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-500 text-white text-[10px] font-semibold hover:bg-emerald-600 disabled:opacity-50"
        >
          <Send className="h-2.5 w-2.5" />
          {saved ? '已記錄' : '送出'}
        </button>
      </div>
      {err && <p className="text-[10px] text-rose-500 mt-1">{err}</p>}
      {item.reference_answer && (
        <div className="mt-2">
          {reveal ? (
            <div className="rounded-md bg-emerald-50/60 border border-emerald-200 p-2">
              <div className="text-[10px] font-semibold text-emerald-700 mb-1">參考答案</div>
              <div className="text-[11px] text-slate-700 leading-relaxed"><MathContent>{item.reference_answer}</MathContent></div>
            </div>
          ) : (
            <button
              onClick={() => setReveal(true)}
              className="text-[10px] text-emerald-600 font-semibold hover:text-emerald-700"
            >
              顯示參考答案
            </button>
          )}
        </div>
      )}
    </li>
  );
}
