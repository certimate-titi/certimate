/**
 * @file 路由 `/super-admin/reverse-engineering` — 考綱逆向工程操作頁（Spec 26）。
 *
 * Super Admin 為某科目觸發 LLM 從考古題反推知識結構：
 * - 全量 extract（重建整棵知識樹）
 * - 增量 incremental（只處理新增考古題）
 * - 預覽當前知識樹
 */
'use client';

import { useEffect, useState } from 'react';
import { Wrench, Loader2, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';
import { reverseEngineeringService, subjectService } from '@/lib/api/services';

export default function ReverseEngineeringPage() {
  const [subjects, setSubjects] = useState<Array<{ id: string; name: string }>>([]);
  const [selected, setSelected] = useState<string>('');
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [tree, setTree] = useState<Array<Record<string, unknown>> | null>(null);

  useEffect(() => {
    subjectService.getUserSubjects().then((res) => {
      const list = (res.subjects || []).map((s) => ({ id: s.subjectId || s.id, name: s.subjectName || s.id }));
      setSubjects(list);
      if (list.length) setSelected(list[0].id);
    }).catch(() => { /* silent */ });
  }, []);

  const run = async (action: 'extract' | 'incremental' | 'preview') => {
    if (!selected) return;
    setBusy(action);
    setMsg(null);
    try {
      if (action === 'extract') {
        const res = await reverseEngineeringService.extract(selected);
        setMsg({ ok: true, text: `✅ 全量萃取完成：${res.nodes_created} 個知識節點` });
      } else if (action === 'incremental') {
        const res = await reverseEngineeringService.incremental(selected);
        setMsg({ ok: true, text: `✅ 增量處理完成：新增 ${res.added} 個節點` });
      } else {
        const res = await reverseEngineeringService.getKnowledgeTree(selected);
        setTree(res.tree || []);
        setMsg({ ok: true, text: `✅ 載入完成（${(res.tree || []).length} 節點）` });
      }
    } catch (e: unknown) {
      const err = e as { message?: string };
      setMsg({ ok: false, text: `❌ ${err?.message || '操作失敗'}` });
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-2 mb-2">
        <Wrench className="w-6 h-6 text-indigo-500" />
        <h1 className="text-2xl font-bold text-slate-900">考綱逆向工程</h1>
      </div>
      <p className="text-sm text-slate-500 mb-6 leading-relaxed">
        Spec 26 §考綱逆向工程：對某科目觸發 LLM 從考古題反推知識結構。
        全量會重建整棵樹（耗時 1-3 分鐘），增量只處理新增考古題。
      </p>

      <div className="bg-white border border-slate-200 rounded-xl p-5 mb-4">
        <label className="block text-xs text-slate-600 mb-2">選擇科目</label>
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className="w-full px-3 py-2 border border-slate-200 rounded text-sm mb-4"
        >
          {subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>

        <div className="grid grid-cols-3 gap-2 mb-4">
          <button
            onClick={() => run('extract')}
            disabled={!selected || busy !== null}
            className="px-3 py-2 bg-rose-500 text-white rounded text-xs font-medium hover:bg-rose-600 disabled:opacity-50 flex items-center justify-center gap-1"
          >
            {busy === 'extract' ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
            全量萃取
          </button>
          <button
            onClick={() => run('incremental')}
            disabled={!selected || busy !== null}
            className="px-3 py-2 bg-emerald-500 text-white rounded text-xs font-medium hover:bg-emerald-600 disabled:opacity-50 flex items-center justify-center gap-1"
          >
            {busy === 'incremental' ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
            增量處理
          </button>
          <button
            onClick={() => run('preview')}
            disabled={!selected || busy !== null}
            className="px-3 py-2 bg-slate-500 text-white rounded text-xs font-medium hover:bg-slate-600 disabled:opacity-50 flex items-center justify-center gap-1"
          >
            預覽知識樹
          </button>
        </div>

        {msg && (
          <div className={`flex items-start gap-2 p-3 rounded text-xs ${
            msg.ok ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'
          }`}>
            {msg.ok ? <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0" /> : <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />}
            <div>{msg.text}</div>
          </div>
        )}
      </div>

      {tree && (
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h2 className="text-sm font-bold text-slate-700 mb-3">知識樹預覽（前 50 節點）</h2>
          <ul className="text-xs space-y-1 max-h-96 overflow-y-auto font-mono">
            {tree.slice(0, 50).map((n, i) => (
              <li key={i} className="text-slate-600 truncate">
                {String(n.depth || 0)} - {String(n.name || '')}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
