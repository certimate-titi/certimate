/**
 * @file 路由 `/super-admin/knowledge-merge` — 知識樹合併衝突解決頁（Spec 29）。
 *
 * Super Admin 處理多資源合併時的節點衝突：
 * - 列出某科目的未解決衝突
 * - 對每筆衝突選擇解決策略：use_source / use_target / merge_both / reject
 * - 顯示合併歷史
 */
'use client';

import { useEffect, useState } from 'react';
import { GitMerge, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { knowledgeMergeService, subjectService, type MergeConflict } from '@/lib/api/services';

type Decision = 'use_source' | 'use_target' | 'merge_both' | 'reject';

const DECISION_LABEL: Record<Decision, string> = {
  use_source: '使用來源',
  use_target: '使用目標',
  merge_both: '合併兩者',
  reject: '拒絕合併',
};

export default function KnowledgeMergePage() {
  const [subjects, setSubjects] = useState<Array<{ id: string; name: string }>>([]);
  const [selected, setSelected] = useState<string>('');
  const [conflicts, setConflicts] = useState<MergeConflict[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  useEffect(() => {
    subjectService.getUserSubjects().then((res) => {
      const list = (res.subjects || []).map((s) => ({ id: s.subjectId || s.id, name: s.subjectName || s.id }));
      setSubjects(list);
      if (list.length) setSelected(list[0].id);
    }).catch(() => { /* silent */ });
  }, []);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    knowledgeMergeService.listConflicts(selected)
      .then((res) => setConflicts((res.conflicts || []).filter((c) => !c.resolved)))
      .catch(() => setConflicts([]))
      .finally(() => setLoading(false));
  }, [selected]);

  const resolve = async (id: string, decision: Decision) => {
    setBusy(id);
    setMsg(null);
    try {
      await knowledgeMergeService.resolve(id, decision);
      setConflicts((prev) => prev.filter((c) => c.id !== id));
      setMsg({ ok: true, text: `✅ 已解決衝突（${DECISION_LABEL[decision]}）` });
    } catch (e: unknown) {
      const err = e as { message?: string };
      setMsg({ ok: false, text: `❌ ${err?.message || '解決失敗'}` });
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-2 mb-2">
        <GitMerge className="w-6 h-6 text-purple-500" />
        <h1 className="text-2xl font-bold text-slate-900">知識樹合併對齊</h1>
      </div>
      <p className="text-sm text-slate-500 mb-6 leading-relaxed">
        Spec 29 §知識樹合併對齊：多資源合併時的節點衝突由 admin 解決。
      </p>

      <div className="bg-white border border-slate-200 rounded-xl p-5 mb-4">
        <label className="block text-xs text-slate-600 mb-2">選擇科目</label>
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className="w-full px-3 py-2 border border-slate-200 rounded text-sm"
        >
          {subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
      </div>

      {msg && (
        <div className={`mb-4 flex items-start gap-2 p-3 rounded text-xs ${
          msg.ok ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'
        }`}>
          {msg.ok ? <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0" /> : <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />}
          <div>{msg.text}</div>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
        </div>
      ) : conflicts.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border border-slate-200">
          <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
          <p className="text-sm text-slate-500 font-medium">此科目目前無未解決衝突 ✨</p>
        </div>
      ) : (
        <div className="space-y-3">
          {conflicts.map((c) => (
            <div key={c.id} className="bg-white border border-amber-200 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs px-2 py-0.5 rounded bg-amber-100 text-amber-700 font-medium">
                  {c.conflict_type}
                </span>
                <span className="text-[10px] text-slate-400">
                  偵測於 {new Date(c.detected_at).toLocaleString('zh-TW')}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-3 mb-3 text-xs">
                <div className="bg-slate-50 p-2 rounded">
                  <div className="text-slate-400 mb-0.5">來源節點</div>
                  <div className="font-medium text-slate-900 truncate">{c.source_node?.name}</div>
                </div>
                <div className="bg-slate-50 p-2 rounded">
                  <div className="text-slate-400 mb-0.5">目標節點</div>
                  <div className="font-medium text-slate-900 truncate">{c.target_node?.name}</div>
                </div>
              </div>
              <div className="flex gap-1.5 flex-wrap">
                {(['use_source', 'use_target', 'merge_both', 'reject'] as Decision[]).map((d) => (
                  <button
                    key={d}
                    onClick={() => resolve(c.id, d)}
                    disabled={busy === c.id}
                    className={`px-3 py-1.5 text-[11px] rounded font-medium transition-colors ${
                      d === 'reject'
                        ? 'bg-rose-100 text-rose-700 hover:bg-rose-200'
                        : 'bg-slate-100 text-slate-700 hover:bg-emerald-100 hover:text-emerald-700'
                    } disabled:opacity-50`}
                  >
                    {busy === c.id ? <Loader2 className="w-3 h-3 animate-spin inline" /> : DECISION_LABEL[d]}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
