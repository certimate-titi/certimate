'use client';

import { useEffect, useState } from 'react';
import { NotebookPen, Download, Sparkles } from 'lucide-react';
import { knowledgeService, type NodeScaffoldItem } from '@/lib/api/services';

export interface ScaffoldNotebookProps {
  nodeId: string | null;
  nodeLabel: string | null;
  isPro: boolean;
  onUpgradeClick?: () => void;
}

export default function ScaffoldNotebook({ nodeId, nodeLabel, isPro, onUpgradeClick }: ScaffoldNotebookProps) {
  const [entries, setEntries] = useState<NodeScaffoldItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [paywall, setPaywall] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!nodeId) {
      setEntries([]);
      return;
    }
    if (!isPro) {
      setPaywall(true);
      return;
    }
    setPaywall(false);
    setLoading(true);
    knowledgeService
      .getNodeScaffolds(nodeId)
      .then((res) => {
        const withResponses = (res.scaffolds || []).filter((s) => s.user_response);
        setEntries(withResponses);
      })
      .catch((err: unknown) => {
        const e = err as { status?: number; message?: string };
        if (e.status === 403) setPaywall(true);
        else setError(e.message || '載入筆記失敗');
      })
      .finally(() => setLoading(false));
  }, [nodeId, isPro]);

  function handleExport() {
    if (entries.length === 0) return;
    const lines: string[] = [`# ${nodeLabel || '節點筆記'}`, ''];
    for (const e of entries) {
      if (e.chapter_heading) lines.push(`## ${e.chapter_heading}`);
      lines.push(`**提問：** ${e.content}`, '');
      lines.push(`**我的筆記：**`, e.user_response || '', '');
      if (e.reference_answer) lines.push(`**參考答案：**`, e.reference_answer, '');
      if (e.responded_at) lines.push(`_記錄時間：${new Date(e.responded_at).toLocaleString('zh-TW')}_`, '');
      lines.push('---', '');
    }
    const blob = new Blob([lines.join('\n')], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${nodeLabel || 'notebook'}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (!nodeId) {
    return (
      <div className="p-4 text-xs text-slate-400 text-center">
        <NotebookPen className="h-6 w-6 mx-auto mb-2 text-slate-300" />
        點擊節點以查看筆記
      </div>
    );
  }

  if (paywall) {
    return (
      <div className="p-4">
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-center">
          <Sparkles className="h-6 w-6 text-amber-500 mx-auto mb-2" />
          <p className="text-xs text-slate-700 font-semibold mb-1">筆記本為 PRO 專屬</p>
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

  if (entries.length === 0) {
    return (
      <div className="p-4 text-xs text-slate-400 text-center">
        <NotebookPen className="h-6 w-6 mx-auto mb-2 text-slate-300" />
        <p>尚無筆記</p>
        <p className="mt-1 text-[10px]">到「教材」深讀模式回答提問，將自動建立筆記</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-slate-200 px-3 py-2 shrink-0">
        <span className="text-[11px] text-slate-500">{entries.length} 則筆記</span>
        <button
          onClick={handleExport}
          className="inline-flex items-center gap-1 text-[11px] text-emerald-600 font-medium hover:text-emerald-700"
        >
          <Download className="h-3 w-3" /> 匯出 Markdown
        </button>
      </div>
      <ul className="flex-1 overflow-y-auto p-3 space-y-2">
        {entries.map((e) => (
          <li key={e.id} className="rounded-lg border border-slate-200 bg-white p-3">
            {e.chapter_heading && (
              <div className="text-[10px] font-semibold text-emerald-600 mb-1">{e.chapter_heading}</div>
            )}
            <p className="text-[11px] font-semibold text-slate-700 mb-1">{e.content}</p>
            <div className="mt-1 rounded bg-slate-50 border border-slate-100 px-2 py-1.5">
              <p className="text-[11px] text-slate-700 whitespace-pre-line leading-relaxed">{e.user_response}</p>
            </div>
            {e.responded_at && (
              <div className="mt-1.5 text-[10px] text-slate-400">
                {new Date(e.responded_at).toLocaleString('zh-TW')}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
