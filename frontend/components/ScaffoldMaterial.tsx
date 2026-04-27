/**
 * @file 學習鷹架教材元件——以快讀 / 深讀兩模式呈現節點對應的 takeaway 與 elaborative 鷹架。
 */
'use client';

import { useEffect, useState } from 'react';
import { BookOpen, Zap, Telescope, Send, Sparkles } from 'lucide-react';
import { knowledgeService, scaffoldService, type NodeScaffoldItem } from '@/lib/api/services';

/** 教材閱讀模式：speed（快讀重點）或 deep（深讀提問）。 */
export type ReadMode = 'speed' | 'deep';

/**
 * ScaffoldMaterial 的 props。
 */
export interface ScaffoldMaterialProps {
  /** 當前節點 ID；null 時顯示提示 */
  nodeId: string | null;
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
export default function ScaffoldMaterial({ nodeId, isPro, onUpgradeClick }: ScaffoldMaterialProps) {
  const [mode, setMode] = useState<ReadMode>('speed');
  const [scaffolds, setScaffolds] = useState<NodeScaffoldItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paywall, setPaywall] = useState(false);

  useEffect(() => {
    if (!nodeId) {
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
    knowledgeService
      .getNodeScaffolds(nodeId)
      .then((res) => setScaffolds(res.scaffolds || []))
      .catch((err: unknown) => {
        const e = err as { status?: number; message?: string };
        if (e.status === 403) setPaywall(true);
        else setError(e.message || '載入教材失敗');
      })
      .finally(() => setLoading(false));
  }, [nodeId, isPro]);

  if (!nodeId) {
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
    return (
      <div className="p-4 text-xs text-slate-400 text-center">
        <BookOpen className="h-6 w-6 mx-auto mb-2 text-slate-300" />
        此節點尚未對應到教材鷹架
      </div>
    );
  }

  const takeaways = scaffolds.filter((s) => s.type === 'takeaway');
  const elaboratives = scaffolds.filter((s) => s.type === 'elaborative');

  return (
    <div className="flex h-full flex-col">
      <div className="flex border-b border-slate-200 px-2 pt-2 gap-1 shrink-0">
        <button
          onClick={() => setMode('speed')}
          className={`flex items-center gap-1 px-3 py-1.5 rounded-t-md text-[11px] font-medium transition-colors ${
            mode === 'speed' ? 'bg-emerald-50 text-emerald-700 border-b-2 border-emerald-500' : 'text-slate-500 hover:text-slate-700'
          }`}
        >
          <Zap className="h-3 w-3" /> 快讀
        </button>
        <button
          onClick={() => setMode('deep')}
          className={`flex items-center gap-1 px-3 py-1.5 rounded-t-md text-[11px] font-medium transition-colors ${
            mode === 'deep' ? 'bg-emerald-50 text-emerald-700 border-b-2 border-emerald-500' : 'text-slate-500 hover:text-slate-700'
          }`}
        >
          <Telescope className="h-3 w-3" /> 深讀
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-3">
        {mode === 'speed' ? (
          <SpeedMode items={takeaways} />
        ) : (
          <DeepMode items={elaboratives} />
        )}
      </div>
    </div>
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
          <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-line">{s.content}</p>
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
      <p className="text-xs font-semibold text-slate-800 mb-2 leading-relaxed">{item.content}</p>
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
              <p className="text-[11px] text-slate-700 leading-relaxed whitespace-pre-line">{item.reference_answer}</p>
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
