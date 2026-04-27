/**
 * @file 路由 `/super-admin/default-resources` — 官方預設資源管理頁。
 *
 * Super Admin 專屬：管理各科目綁定的官方預設學習資源（official_default badge）。
 */
'use client';

import { useEffect, useState } from 'react';
import { Plus, Trash2, Link as LinkIcon } from 'lucide-react';
import { adminDefaultResourceService } from '@/lib/api/services';
import { apiClient } from '@/lib/api/client';
import { useAuth } from '@/lib/auth-context';

interface Subject {
  id: string;
  name: string;
}
interface Resource {
  id: string;
  name: string;
  scope?: string;
}

export default function DefaultResourcesPage() {
  const { isAdmin, loading: authLoading } = useAuth();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [platformResources, setPlatformResources] = useState<Resource[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState('');
  const [selectedResourceId, setSelectedResourceId] = useState('');
  const [bindings, setBindings] = useState<
    Array<{ subject_id: string; resource_id: string; subject_name?: string; resource_name?: string }>
  >([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading || !isAdmin) return;
    (async () => {
      try {
        const sRes = await apiClient.get<{ subjects?: Subject[]; categories?: Array<{ subjects: Subject[] }> }>(
          '/subjects/available',
        );
        const flat = sRes.subjects || (sRes.categories || []).flatMap((c) => c.subjects || []);
        setSubjects(flat);

        const rRes = await apiClient.get<{ resources?: Array<Resource & { scope?: string }> }>('/resources');
        setPlatformResources((rRes.resources || []).filter((r) => r.scope === 'platform'));
      } catch (e: unknown) {
        setMsg(e instanceof Error ? e.message : '載入失敗');
      }
    })();
  }, [authLoading, isAdmin]);

  const bind = async () => {
    if (!selectedSubjectId || !selectedResourceId) return;
    setBusy(true);
    setMsg(null);
    try {
      await adminDefaultResourceService.bindDefault(selectedSubjectId, selectedResourceId);
      const s = subjects.find((x) => x.id === selectedSubjectId);
      const r = platformResources.find((x) => x.id === selectedResourceId);
      setBindings((prev) => [
        ...prev,
        {
          subject_id: selectedSubjectId,
          resource_id: selectedResourceId,
          subject_name: s?.name,
          resource_name: r?.name,
        },
      ]);
      setMsg('綁定成功');
    } catch (e: unknown) {
      setMsg(e instanceof Error ? e.message : '綁定失敗');
    } finally {
      setBusy(false);
    }
  };

  const unbind = async (subject_id: string, resource_id: string) => {
    if (!confirm('確定解除此預設資源綁定？')) return;
    setBusy(true);
    try {
      await adminDefaultResourceService.unbindDefault(subject_id, resource_id);
      setBindings((prev) => prev.filter((b) => !(b.subject_id === subject_id && b.resource_id === resource_id)));
    } catch (e: unknown) {
      setMsg(e instanceof Error ? e.message : '解除失敗');
    } finally {
      setBusy(false);
    }
  };

  if (authLoading) return <div className="p-8 text-slate-500">載入中…</div>;
  if (!isAdmin)
    return <div className="p-8 text-red-600">需要管理員權限</div>;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-slate-900 mb-1">預設資源綁定</h1>
      <p className="text-sm text-slate-600 mb-6">
        把 scope=platform 的資源綁定為某考科的預設資源，所有用戶選該考科時自動可見（唯讀）。PRD-033 US-04。
      </p>

      <div className="bg-white rounded-2xl border border-slate-200 p-5 mb-6">
        <h2 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
          <LinkIcon className="w-4 h-4" /> 新增綁定
        </h2>
        <div className="grid md:grid-cols-2 gap-3 mb-3">
          <div>
            <label className="block text-xs text-slate-600 mb-1">考科</label>
            <select
              value={selectedSubjectId}
              onChange={(e) => setSelectedSubjectId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white text-sm"
            >
              <option value="">— 選擇考科 —</option>
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-600 mb-1">平台資源（scope=platform）</label>
            <select
              value={selectedResourceId}
              onChange={(e) => setSelectedResourceId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white text-sm"
            >
              <option value="">— 選擇資源 —</option>
              {platformResources.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          </div>
        </div>
        <button
          onClick={bind}
          disabled={busy || !selectedSubjectId || !selectedResourceId}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-900 text-white text-sm disabled:opacity-50"
        >
          <Plus className="w-4 h-4" /> 綁定
        </button>
        {msg && <div className="mt-3 text-sm text-slate-600">{msg}</div>}
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-5">
        <h2 className="font-semibold text-slate-900 mb-3">本 Session 新增的綁定</h2>
        {bindings.length === 0 ? (
          <p className="text-sm text-slate-400">尚無綁定紀錄（載入既有綁定需額外 API）</p>
        ) : (
          <div className="space-y-2">
            {bindings.map((b, i) => (
              <div
                key={`${b.subject_id}-${b.resource_id}-${i}`}
                className="flex items-center justify-between p-3 rounded-lg bg-slate-50 text-sm"
              >
                <div>
                  <span className="font-medium">{b.subject_name || b.subject_id}</span>
                  <span className="mx-2 text-slate-400">←</span>
                  <span className="text-slate-700">{b.resource_name || b.resource_id}</span>
                </div>
                <button
                  onClick={() => unbind(b.subject_id, b.resource_id)}
                  className="p-1.5 rounded-md text-slate-400 hover:text-red-600 hover:bg-red-50"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
